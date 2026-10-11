"""Compute overlay entry points from thunks (host side).

For each thunk (word=w -> target T): if row w is placed at address A with
real arena base B, then entry = A + (T - B)   [record loads at arena +0, finding 18]

Writes analysis/ida_falconcd/overlay_entries.json:
  [{row, thunk_word, target_linear, entry_ea, seg_name}, ...]
"""
import json
import struct
from pathlib import Path

EXE = Path('game/FALCONCD.EXE').read_bytes()
THUNK = 0x1EBAF

placements = {p['idx']: p for p in json.load(open('analysis/ida_falconcd/overlay_placement.json'))}

entries = []
seen = set()
for i in range(400):
    o = THUNK + i * 10
    if o + 10 > len(EXE) or EXE[o] != 0xE8 or EXE[o + 3] != 0xEA:
        break
    loff, lseg, wid = struct.unpack_from('<HHH', EXE, o + 4)
    target = ((0x1000 + lseg) << 4) + loff
    p = placements.get(wid)
    if not p or p['addr'] == 'skip' or p['addr'] == 'real' and not p['ida_len']:
        continue
    if p['addr'] == 'skip' or not p['ida_len']:
        continue
    real_base = p['real_ea']
    if not (real_base <= target < real_base + p['span_bytes']):
        # target outside this row's block - still try with recorded length
        pass
    rel = target - real_base
    if rel < 0:
        continue
    entry = p['ida_ea'] + rel
    key = (wid, entry)
    if key in seen:
        continue
    seen.add(key)
    entries.append(dict(row=wid, thunk_word=wid, target_linear=target,
                        entry_ea=entry, seg_name=p['seg_name'],
                        in_len=(rel < p['ida_len'])))

out = [e for e in entries if e['in_len']]
json.dump(out, open('analysis/ida_falconcd/overlay_entries.json', 'w'), indent=1)
print('entries computed: %d (in-bounds %d, dropped %d)' % (
    len(entries), len(out), len(entries) - len(out)))
from collections import Counter
print('per-row:', dict(Counter(e['row'] for e in out)))
