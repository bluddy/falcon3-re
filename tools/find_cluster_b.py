"""Locate cluster-B records (rows 50-69) in the file.

Their w2 values (0x6D..0x39B0) break the main w2-chain, so their windows use an
unknown base B0: window = B0 + w2*16. Find B0 by scanning for row50's fixup table
(466 dword pairs whose segs lie in row50's block [0x569F, 0x569F+span_p)).

Strategy: stride-16 scan of the post-chain region (and whole file as fallback)
scoring candidate positions; on hit, verify the tiling chain rows50..69.
"""
import json
import struct
from pathlib import Path

EXE = Path('game/FALCONCD.EXE').read_bytes()
DIR = 0x1E24F

rows = {}
for i in range(70):
    o = DIR + i * 18
    w0, w1, w2, w3, w4, w5, w6, w7, w8 = struct.unpack_from('<9H', EXE, o)
    rows[i] = dict(idx=i, w0=w0, w2=w2, span=w4, fixups=w5)

r50 = rows[50]
N = r50['fixups']
SPAN_P = r50['span']
lo, hi = r50['w0'], r50['w0'] + SPAN_P

def score(p):
    if p + N * 4 > len(EXE):
        return 0.0
    ok = 0
    sample = min(N, 48)
    for k in range(sample):
        seg = struct.unpack_from('<H', EXE, p + k * 4 + 2)[0]
        if lo <= seg < hi:
            ok += 1
    fs = ok / sample
    if fs < 0.5:
        return fs
    ok = 0
    for k in range(N):
        seg = struct.unpack_from('<H', EXE, p + k * 4 + 2)[0]
        if lo <= seg < hi:
            ok += 1
    return ok / N

# main chain ends around 0xFF730; cluster windows span w2*16 in [0x6D0, 0x39B00]
# candidate table starts = B0 + w2*16 for unknown B0 -> scan regions where such a
# run could live: [0x0, file_end - N*4] stride 16, prioritize after chain end.
cands = list(range(0xFF000, min(len(EXE) - N * 4, 0x14F5E7), 16))
best = (0, 0)
for p in cands:
    s = score(p)
    if s > best[1]:
        best = (p, s)
        if s >= 0.9:
            break
print('post-chain scan best: pos=0x%X score=%.3f' % best)

if best[1] < 0.8:
    # full fallback, coarser
    for p in range(0, min(len(EXE) - N * 4, 0x14F5E7), 16):
        s = score(p)
        if s > best[1]:
            best = (p, s)
            if s >= 0.9:
                break
    print('full scan best: pos=0x%X score=%.3f' % best)

if best[1] >= 0.8:
    # derive B0: table pos should be B0 + w2*16 (fixups-first) OR after data (data-first)
    table_pos = best[0]
    B0_a = table_pos - (r50['w2'] << 4)
    print('candidate B0 (fixups-first): 0x%X' % B0_a)
    # verify chain: for each cluster row, window = B0 + w2<<4 must be increasing and tile
    seq = sorted(range(50, 70), key=lambda i: rows[i]['w2'])
    prev_end = None
    ok = True
    plan = []
    for i in seq:
        r = rows[i]
        w = B0_a + (r['w2'] << 4)
        # estimate window: span*16 + fixups*4
        win = r['span'] * 16 + ((r['fixups'] * 4 + 15) // 16) * 16
        # data-first vs fixups-first: check fixup validity at w
        ov = set(range(r['w0'], r['w0'] + max(1, r['span']))) | {0x1D0D, 0x1D31}
        fp = w
        need = r['fixups'] * 4
        if fp + need <= len(EXE) and r['fixups']:
            frac = sum(1 for k in range(r['fixups'])
                       if struct.unpack_from('<H', EXE, fp + k * 4 + 2)[0] in ov) / r['fixups']
        else:
            frac = 0.0
        plan.append(dict(idx=i, window=w, fixup_frac_at_window=round(frac, 2)))
        print('  row%-3d w2=%-6X window=0x%-8X fixfrac=%.2f' % (i, r['w2'], w, frac))
    print('done')
else:
    print('NOT FOUND - cluster B base unresolved')
