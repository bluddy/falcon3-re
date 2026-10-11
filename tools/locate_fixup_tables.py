"""Locate each row's fixup table by scanning for a run of valid (off,seg) dwords.

Candidate windows per row:
  W1: file_off = w2 * 16                      (gunship/para base)
  W2: file_off = 0x1FB50 + w2 * 16            (tail para base)
  W3: file_off = 0x1FB51 + w2                 (old tail-relative)
Window length = align16(span*16) + fixups*4 + 0x100 (bounded by file).

A position P matches if dwords[P..P+B) have seg field in OVERLAY_SEGS for >=80%.
Report per row: window found, exact fixup pos, data pos (before or after table),
and the inferred data span consistency: A*16 == distance data -> next window.
"""
import json
import struct
from pathlib import Path

EXE = Path('game/FALCONCD.EXE').read_bytes()
TAIL = 0x1FB51
TAIL_PARA = 0x1FB50
DIR_FILE = 0x1E24F

rows = []
for i in range(70):
    o = DIR_FILE + i * 18
    w0, w1, w2, w3, w4, w5, w6, w7, w8 = struct.unpack_from('<9H', EXE, o)
    rows.append(dict(idx=i, w0=w0, w2=w2, flags=w3 >> 8, span=w4,
                     fixups=w5, id=w7, dsize=w8))

OVSET = {r['w0'] for r in rows} | {0x1D0D, 0x1D31, 0x1EFE}


def score_at(p, count):
    if count == 0:
        return 1.0
    need = count * 4
    if p < 0 or p + need > len(EXE):
        return 0.0
    sample = min(count, 64)
    ok = 0
    for k in range(sample):
        seg = struct.unpack_from('<H', EXE, p + k * 4 + 2)[0]
        if seg in OVSET:
            ok += 1
    frac_s = ok / sample
    if frac_s < 0.5:
        return frac_s
    ok = 0
    for k in range(count):
        seg = struct.unpack_from('<H', EXE, p + k * 4 + 2)[0]
        if seg in OVSET:
            ok += 1
    return ok / count


def find_table(win_start, win_len, count, span, fix):
    """Structured candidates first, then coarse scan."""
    align_fix = ((fix + 15) // 16) * 16
    cands = [win_start, win_start + align_fix, win_start + span,
             win_start + span + align_fix, win_start + fix]
    best = (win_start, 0.0)
    for p in cands:
        s = score_at(p, count)
        if s >= 0.8:
            return p, s
        if s > best[1]:
            best = (p, s)
    # coarse fallback scan (stride 16, bounded)
    step = max(16, win_len // 2048)
    p = win_start
    limit = win_start + max(1, win_len - count * 4)
    while p <= limit and p < len(EXE):
        s = score_at(p, count)
        if s >= 0.8:
            return p, s
        if s > best[1]:
            best = (p, s)
        p += step
    return best


# window ends: next smaller-greater w2*16 among rows... build sorted para bases
paras = sorted({r['w2'] << 4 for r in rows if r['w2'] >= 0x1000} |
               {TAIL_PARA + (r['w2'] << 4) for r in rows if r['w2'] < 0x1000})

out = []
for r in rows:
    span_bytes = r['span'] * 16
    fix_bytes = r['fixups'] * 4
    cands = []
    if r['w2'] >= 0x1000:
        cands.append(('W1', r['w2'] << 4))
    else:
        cands.append(('W2', TAIL_PARA + (r['w2'] << 4)))
        cands.append(('W3', TAIL + r['w2']))
        cands.append(('W1b', r['w2'] << 4))
    win_len = span_bytes + fix_bytes + 0x200
    best = None
    for tag, base in cands:
        if base < 0 or base >= len(EXE):
            continue
        pos, frac = find_table(base, win_len, r['fixups'], span_bytes, fix_bytes) if r['fixups'] else (base, 1.0)
        if best is None or frac > best[3]:
            best = (tag, base, pos, frac)
    tag, base, pos, frac = best
    # data side: if table at window start -> data after align16(fixbytes)
    #            if table later -> data at window start
    if pos == base:
        data = base + ((fix_bytes + 15) // 16) * 16
        order = 'fixups-first'
    else:
        data = base
        order = 'data-first'
    out.append(dict(idx=r['idx'], w0=r['w0'], w2=r['w2'], window=tag,
                    base=base, fixup_pos=pos, fixup_frac=round(frac, 2),
                    data=data, order=order, span=span_bytes, fix=fix_bytes))

print('%-3s %-5s %-6s %-4s %-9s %-9s %-4s %-12s %-6s' % (
    'idx', 'w0', 'w2', 'win', 'base', 'fix_pos', 'frac', 'order', 'data'))
for e in out:
    print('%-3d %-5X %-6X %-4s %-9X %-9X %-4.2f %-12s %-6X' % (
        e['idx'], e['w0'], e['w2'], e['window'], e['base'],
        e['fixup_pos'], e['fixup_frac'], e['order'], e['data']))

good = sum(1 for e in out if e['fixup_frac'] >= 0.8)
print('rows with >=80%% valid fixup table: %d/70' % good)
json.dump(out, open('analysis/ida_falconcd/record_fixup_located.json', 'w'), indent=1)
print('wrote analysis/ida_falconcd/record_fixup_located.json')
