"""ISLDAT full parser + cross-theater validation (canonical format check).

Format (docs/structures.md section ISLDAT, finding 105):

  header 9B: u16 body_len(=size-9) | u16 0 | u16 t1_base(always 0x500) |
             u16 t2_base(0x504..0x7CA) | u8 swap_flag (state_table_apply only)
  body (loaded at seg:0000, walk base word_11C16 = 0):
    gridB fine   4 quadrants @ 0x000+q*0x100, idx=(X&~1)*8+(Y>>1)   byte -> t1 list index
    gridA coarse 4 quadrants @ 0x400+q*0x40,  idx=(X&~3)*2+(Y>>2)   byte -> t2 list index
    t1 table @ t1_base, K1 words (fixed point: min(e[:K]) == base+2K);
         each u16 -> FFFF-terminated list of feature-record offsets (fine pool)
    t2 table @ t2_base, K2 words; lists -> feature-record offsets (coarse pool)
    alt views of grid-B q0 bytes (state_table_apply_71c1, NOT the coastline walk):
         byte @ 0x65+n, 3-byte record @ 0x56+3n (b0/b1 byteswapped if swap_flag)

  feature record:
    +00 i32 X, +04 i32 Y (16.16 nm, world wrap 512), +08 i32 Z (~-50 LSB = sea)
    +0C i32 0
    +1E u16 FFFF
    +20 u16 attr (0x14/0x32/0x64/0xC8 observed)
    +22 u16 = self+0x26, +24 u16 0x000B, +26 u16 FFFF, +28 u16 0
    +2A u16 = self+0x2E, +2C u16 4, +2E u16 point_count
    +30 u16 = self+0x38 (points), +32 u16 = points+6*count (op stream), +34 u16 0
    points: count x {i16 p0, i16 p1(always 0 observed), i16 p2}
    op stream: u16 offsets (FFFF-terminated) -> sub-records

  sub-record:
    +00 u16 flags (0x1000/0x1002 = node chain, 0x0000/0x0002 = single node),
         +02 u16 opcode (0x0000/0x0001/0x0002 observed)
    flags & 0x1000: nodes until u16 FFFF; else exactly one node, no terminator
      node = u16 count | (count+1) x u16 line-table offsets (stride 0x10,
             multiples of 0x10, last word == first word = closed ring)
    validated: 196/196 sub-records across all 8 theaters

Consumers (resident asm): pos_neighbor_norm_scan (0x14B17) grid walks ->
pos_diff_norm (0x28874) -> line_draw_441e (0x28B08) builds es:441E entries ->
op-stream loop -> loc_2978E (0x2978E) -> line_table_build_dispatch (0x29B82) /
record_span_mask_rebuild (0x299D5) / record_span_build_and_dispatch (0x29917).
"""
import struct, sys, glob

def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def i16(b, o): return struct.unpack_from('<h', b, o)[0]
def i32(b, o): return struct.unpack_from('<i', b, o)[0]

class Rep:
    def __init__(self): self.errs = []; self.warns = []
    def err(self, m): self.errs.append(m)
    def warn(self, m): self.warns.append(m)

def table_extent(body, base, limit, rep, name):
    """K where min(u16[0..K-1]) == base+2K (first list starts right after table)."""
    best = None
    for K in range(1, (limit - base) // 2 + 1):
        vals = [u16(body, base + 2 * j) for j in range(K)]
        if min(vals) == base + 2 * K:
            best = K
    if best is None:
        rep.err('%s: no fixed-point extent' % name)
        return []
    return [u16(body, base + 2 * j) for j in range(best)]

def read_list(body, ptr, rep, name):
    out = []
    o = ptr
    while True:
        if o + 2 > len(body):
            rep.err('%s: list @0x%X unterminated' % (name, ptr)); return out
        v = u16(body, o); o += 2
        if v == 0xFFFF: return out
        if v >= len(body):
            rep.err('%s: list @0x%X entry 0x%X out of body' % (name, ptr, v)); return out
        out.append(v)

def parse_record(body, off, rep):
    if off + 0x36 > len(body):
        rep.err('rec 0x%X truncated' % off); return None
    d = dict(off=off,
             x=i32(body, off) / 65536.0, y=i32(body, off + 4) / 65536.0,
             z=i32(body, off + 8) / 65536.0,
             attr=u16(body, off + 0x20), count=u16(body, off + 0x2E),
             pb=u16(body, off + 0x30), ob=u16(body, off + 0x32))
    if abs(d['x']) > 513 or abs(d['y']) > 513:
        rep.err('rec 0x%X coord out of world (%.1f,%.1f)' % (off, d['x'], d['y']))
    if u16(body, off + 0x1E) != 0xFFFF: rep.err('rec 0x%X +1E not FFFF' % off)
    if u16(body, off + 0x22) != (off + 0x26) & 0xFFFF: rep.err('rec 0x%X +22 != self+0x26' % off)
    if u16(body, off + 0x26) != 0xFFFF: rep.err('rec 0x%X +26 not FFFF' % off)
    if u16(body, off + 0x2A) != (off + 0x2E) & 0xFFFF: rep.err('rec 0x%X +2A != self+0x2E' % off)
    if d['pb'] != (off + 0x38) & 0xFFFF:
        rep.err('rec 0x%X points 0x%X != self+0x38' % (off, d['pb']))
    if d['ob'] != (d['pb'] + 6 * d['count']) & 0xFFFF:
        rep.err('rec 0x%X ops 0x%X != points+6*count' % (off, d['ob']))
    # points
    n = d['count']
    if d['pb'] + 6 * n > len(body):
        rep.err('rec 0x%X points overrun' % off); return d
    d['mid_zero'] = all(i16(body, d['pb'] + 6 * i + 2) == 0 for i in range(n))
    # op stream -> sub-records -> nodes
    o = d['ob']; d['nsubs'] = 0; d['nnodes'] = 0
    while True:
        if o + 2 > len(body): rep.err('rec 0x%X opstream overrun' % off); break
        v = u16(body, o); o += 2
        if v == 0xFFFF: break
        if v + 4 > len(body): rep.err('rec 0x%X sub @0x%X out of body' % (off, v)); break
        d['nsubs'] += 1
        flags, op = u16(body, v), u16(body, v + 2)
        d.setdefault('flagset', set()).add(flags)
        d.setdefault('opset', set()).add(op)
        p = v + 4
        chain = flags & 0x1000
        while True:
            if p + 2 > len(body): rep.err('rec 0x%X node overrun' % off); break
            cnt = u16(body, p)
            if cnt == 0xFFFF:
                if not chain: rep.err('rec 0x%X single-node sub has FFFF' % off)
                p += 2
                break
            need = 2 * (cnt + 2)
            if p + need > len(body): rep.err('rec 0x%X node count %d overrun' % (off, cnt)); break
            payload = [u16(body, p + 2 + 2 * i) for i in range(cnt + 1)]
            bad = [w for w in payload if w % 0x10]
            if bad: rep.err('rec 0x%X node payload not stride-0x10: %s' % (off, bad))
            if cnt and payload[-1] != payload[0]:
                rep.err('rec 0x%X node not closed (%04X..%04X)' % (off, payload[0], payload[-1]))
            d['nnodes'] += 1
            p += need
            if not chain: break
    return d

def parse(path):
    rep = Rep()
    name = path.replace('\\', '/').split('/')[-1]
    raw = open(path, 'rb').read()
    blen, z, t1, t2 = struct.unpack_from('<HHHH', raw, 0)
    swap = raw[8]
    body = raw[9:]
    if blen != len(body): rep.err('header body_len %d != %d' % (blen, len(body)))
    if z != 0: rep.err('header word2 = 0x%X (expected 0)' % z)
    if t1 != 0x500: rep.err('t1 base 0x%X != 0x500' % t1)
    if not (t1 < t2 <= len(body)): rep.err('t2 base 0x%X out of range' % t2)
    e1 = table_extent(body, t1, t2, rep, 't1')
    e2 = table_extent(body, t2, len(body), rep, 't2')
    # grids
    gA = [body[0x400 + q * 0x40:0x440 + q * 0x40] for q in range(4)]
    gB = [body[q * 0x100:(q + 1) * 0x100] for q in range(4)]
    maxA = max((max(g) for g in gA if len(g) == 0x40), default=0)
    maxB = max((max(g) for g in gB if len(g) == 0x100), default=0)
    if maxA >= len(e2): rep.err('gridA max %d >= t2 entries %d' % (maxA, len(e2)))
    if maxB >= len(e1): rep.err('gridB max %d >= t1 entries %d' % (maxB, len(e1)))
    # lists -> records
    r1, r2 = set(), set()
    for ptr in e1: r1.update(read_list(body, ptr, rep, 't1list'))
    for ptr in e2: r2.update(read_list(body, ptr, rep, 't2list'))
    overlap = r1 & r2
    if overlap: rep.warn('pools share %d records' % len(overlap))
    recs = {}
    for off in sorted(r1 | r2):
        d = parse_record(body, off, rep)
        if d: recs[off] = d
    mid_ok = all(d.get('mid_zero') for d in recs.values()) if recs else True
    if not mid_ok: rep.warn('some point middle words != 0')
    flagset, opset = set(), set()
    for d in recs.values():
        flagset |= d.get('flagset', set()); opset |= d.get('opset', set())
    return dict(name=name, size=len(raw), blen=blen, swap=swap, t1=t1, t2=t2,
                k1=len(e1), k2=len(e2), maxA=maxA, maxB=maxB,
                n1=len(r1), n2=len(r2), nrec=len(recs),
                nsub=sum(d.get('nsubs', 0) for d in recs.values()),
                nnod=sum(d.get('nnodes', 0) for d in recs.values()),
                attrs=sorted({d['attr'] for d in recs.values()}),
                flags=sorted(flagset), ops=sorted(opset),
                errs=rep.errs, warns=rep.warns)

def main():
    files = sorted(glob.glob('game/ISLDAT.*'))
    bad = 0
    for p in files:
        r = parse(p)
        status = 'OK  ' if not r['errs'] else 'FAIL'
        if r['errs']: bad += 1
        print('%s %-13s size=%-5d swap=%d t1=0x%03X(%3d) t2=0x%03X(%3d) '
              'gridA<=%-2d gridB<=%-2d recs=%3d/%-3d subs=%-3d nodes=%-3d '
              'attr=%s fl=%s op=%s%s' %
              (status, r['name'], r['size'], r['swap'], r['t1'], r['k1'], r['t2'], r['k2'],
               r['maxA'], r['maxB'], r['n1'], r['n2'], r['nsub'], r['nnod'],
               [hex(a) for a in r['attrs']], [hex(a) for a in r['flags']],
               [hex(a) for a in r['ops']],
               ' warns=%d' % len(r['warns']) if r['warns'] else ''))
        for e in r['errs'][:6]: print('       ERROR:', e)
        for w in r['warns'][:3]: print('       warn:', w)
    print('ALL OK' if not bad else '%d FILES FAILED' % bad)
    return 1 if bad else 0

sys.exit(main())
