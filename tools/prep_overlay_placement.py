"""Precompute overlay record placements for the IDB rebuild (findings 17/18).

For each of the 70 dir rows:
  data_file  - where the record's data bytes live in FALCONCD.EXE
               (from record_fixup_located.json when fixup table located;
                default: fixups-first at w2*16 for w2>=0x1000,
                data-first at 0x1FB50+w2*16 for small w2)
  runtime_ea - (0x1000 + w0) << 4   (arena base, IDA linear)
  len        - span*16 clipped to file window and to the next distinct arena

Address assignment for the IDB (transient overlap!):
  - arenas (unique w0) are clipped against each other (no cross-arena overlap)
  - within an arena only ONE record can hold the real address; the first record
    in dir order keeps it, later same-arena records go to synthetic bases
    (0x100000+, 16-aligned) so all records stay analyzable.
  Mapping recorded in analysis/ida_falconcd/overlay_placement.json.

Output: analysis/ida_falconcd/overlay_placement.json
"""
import json
import struct
from pathlib import Path

EXE = Path('game/FALCONCD.EXE').read_bytes()
DIR = 0x1E24F
TAIL_PARA = 0x1FB50

rows = []
for i in range(70):
    o = DIR + i * 18
    w0, w1, w2, w3, w4, w5, w6, w7, w8 = struct.unpack_from('<9H', EXE, o)
    rows.append(dict(idx=i, w0=w0, w2=w2, flags=w3 >> 8, span=w4,
                     fixups=w5, idf=w7, dsize=w8))

located = {}
lf = Path('analysis/ida_falconcd/record_fixup_located.json')
if lf.exists():
    for e in json.load(open(lf)):
        located[e['idx']] = e

# --- split chain rows (monotonic non-decreasing w2: rows0..49) vs cluster B
# (w2 wraps at row50 -> tails 0x6D..0x39B0). Cluster-B base found 2026-10-11:
# B0 = 0xFFFA0 (window = B0 + w2*16; fixups-first for 50..68; row69 special:
# code-first with fixup table at window+0x60, data len = w8*16)  [finding 20]
CLUSTER_B0 = 0xFFFA0
chain_idx, cluster_b = [], []
prev = -1
for r in rows:
    if r['w2'] >= prev:
        chain_idx.append(r['idx'])
        prev = r['w2']
    else:
        cluster_b.append(r['idx'])

def window_base(r):
    e = located.get(r['idx'])
    if e and e['fixup_frac'] >= 0.8:
        return e['base']
    return r['w2'] << 4

bases = sorted({window_base(r) for r in rows if r['idx'] in chain_idx})

def window_end(r):
    b = window_base(r)
    later = [x for x in bases if x > b]
    return min(later[0], len(EXE)) if later else len(EXE)

placements = []
for r in rows:
    if r['idx'] in cluster_b:
        window = CLUSTER_B0 + (r['w2'] << 4)
        later = [CLUSTER_B0 + (rows[i]['w2'] << 4)
                 for i in cluster_b if rows[i]['w2'] > r['w2']]
        nxt = min(later) if later else len(EXE)
        if r['idx'] == 69:
            # startup record: code-first; fixup table at window+0x60; data = w8*16
            data_file = window
            fixup_pos = window + 0x60
            length = min(r['dsize'] * 16 if 'dsize' in r else r['span'] * 16,
                         len(EXE) - window)
            order = 'code-first(startup)'
        else:
            fixup_pos = window
            data_file = window + ((r['fixups'] * 4 + 15) // 16) * 16
            length = min(r['span'] * 16, max(0, nxt - data_file))
            order = 'clusterB-fixups-first'
        placements.append(dict(idx=r['idx'], w0=r['w0'], flags=r['flags'],
                               real_ea=((0x1000 + r['w0']) << 4),
                               data_file=data_file, length=length,
                               span_bytes=r['span'] * 16, order=order,
                               fixup_frac=None, fixup_pos=fixup_pos,
                               placed=True))
        continue
    e = located.get(r['idx'])
    base_ok = None
    if r['fixups'] and r['idx'] in chain_idx:
        # extended validity at base: segs may be ANY paragraph in [w0, w0+span)
        # (finding 18) plus core paras
        ov = set(range(r['w0'], r['w0'] + max(1, r['span']))) | {0x1D0D, 0x1D31}
        bp = r['w2'] << 4
        need = r['fixups'] * 4
        if bp + need <= len(EXE):
            ok = 0
            for k in range(r['fixups']):
                seg = struct.unpack_from('<H', EXE, bp + k * 4 + 2)[0]
                if seg in ov:
                    ok += 1
            base_ok = ok / r['fixups']
    if base_ok is not None and base_ok >= 0.8:
        # fixups-first at base overrides any located data-first misread
        data_file = (r['w2'] << 4) + ((r['fixups'] * 4 + 15) // 16) * 16
        order = 'fixups-first(base-extended)'
    elif e and e['fixup_frac'] >= 0.8:
        data_file = e['data']
        order = e['order']
    else:
        data_file = (r['w2'] << 4) + ((r['fixups'] * 4 + 15) // 16) * 16
        order = 'fixups-first(default)'
    span_bytes = r['span'] * 16
    wend = window_end(r)
    avail = max(0, wend - data_file)
    length = min(span_bytes, avail)
    placements.append(dict(idx=r['idx'], w0=r['w0'], flags=r['flags'],
                           real_ea=((0x1000 + r['w0']) << 4),
                           data_file=data_file, length=length,
                           span_bytes=span_bytes, order=order,
                           fixup_frac=(e['fixup_frac'] if e else None),
                           placed=True))

# arena clipping: distinct w0 starts sorted; clip real spans at next arena start
starts = sorted({p['real_ea'] for p in placements})
def clip(p):
    later = [s for s in starts if s > p['real_ea']]
    lim = later[0] if later else (0x1000000)
    p['real_len'] = min(p['length'], max(0, lim - p['real_ea']))
for p in placements:
    clip(p)

# address assignment: first PLACED record (length>0) per w0 keeps real; rest synthetic
syn_base = 0x100000
seen_w0 = set()
for p in placements:
    if not p.get('placed') or p['length'] == 0:
        p['ida_ea'] = None
        p['ida_len'] = 0
        p['addr'] = 'skip'
        p['seg_name'] = 'R%02d_%04X_skip' % (p['idx'], p['w0'])
        continue
    if p['w0'] not in seen_w0:
        seen_w0.add(p['w0'])
        p['ida_ea'] = p['real_ea']
        p['ida_len'] = p['real_len']
        p['addr'] = 'real'
    else:
        p['ida_ea'] = syn_base
        p['ida_len'] = p['length']
        p['addr'] = 'synthetic'
        syn_base += (p['length'] + 16 + 15) // 16 * 16
    p['seg_name'] = 'R%02d_%04X%s' % (p['idx'], p['w0'],
                                       '' if p['addr'] == 'real' else 's')

json.dump(placements, open('analysis/ida_falconcd/overlay_placement.json', 'w'), indent=1)

real = sum(1 for p in placements if p['addr'] == 'real')
syn = sum(1 for p in placements if p['addr'] == 'synthetic')
skp = sum(1 for p in placements if p['addr'] == 'skip')
print('placements: %d total = %d real + %d synthetic + %d skipped' % (
    len(placements), real, syn, skp))
print('clusterB (unplaced): %s' % cluster_b)
print('synthetic top: 0x%X' % syn_base)
total_bytes = sum(p['ida_len'] for p in placements if p['ida_len'])
print('total bytes to write: %d' % total_bytes)
json.dump(dict(cluster_b=cluster_b, chain=chain_idx),
          open('analysis/ida_falconcd/overlay_clusters.json', 'w'), indent=1)
print('wrote analysis/ida_falconcd/overlay_placement.json + overlay_clusters.json')
