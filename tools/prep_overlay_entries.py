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
# finding 55/56: the .RTLink thunk table's 10-byte E8..EA run starts at
# 0x1E99D (303 entries .. 0x1F573). 0x1EBAF is entry #053 -- using it skipped
# slots #000..#052. Cross-check: file 0x1E99D -> IDA 0x2BD9D (hdr 0x2C00, so
# IDA = file + 0xD400), which is where patch_thunks_ida.py found the table.
THUNK = 0x1E99D

placements = {p['idx']: p for p in json.load(open('analysis/ida_falconcd/overlay_placement.json'))}
PLACES = list(placements.values())

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
    # finding 56: `in_len` stays row-relative (is the target inside THIS row's
    # written window).  `covered_seg` answers the question that actually gates
    # registration -- is the EA inside ANY record's written window?  Slots #095
    # and #099 land outside their own row but inside R17_5E8F / R19_5F6C.
    cov = next((q['seg_name'] for q in PLACES
                if q.get('ida_ea') is not None and q['ida_len']
                and q['ida_ea'] <= entry < q['ida_ea'] + q['ida_len']), None)
    entries.append(dict(row=wid, thunk_word=wid, target_linear=target,
                        entry_ea=entry, seg_name=p['seg_name'],
                        in_len=(rel < p['ida_len']), covered_seg=cov))

# finding 56: keep EVERY distinct target, including the 3 whose own row does
# not reach them -- dropping them made the table silently incomplete.  The
# registration pass gates on `covered_seg`, not on this list being pre-filtered.
json.dump(entries, open('analysis/ida_falconcd/overlay_entries.json', 'w'), indent=1)
n_in = sum(1 for e in entries if e['in_len'])
n_cov = sum(1 for e in entries if e['covered_seg'])
print('entries computed: %d  (own-row in-bounds %d, covered by SOME record %d, '
      'covered by nothing %d)' % (len(entries), n_in, n_cov, len(entries) - n_cov))
for e in entries:
    if not e['covered_seg']:
        print('   UNCOVERED row=%d target=0x%X entry=0x%X'
              % (e['row'], e['target_linear'], e['entry_ea']))
from collections import Counter
print('per-row:', dict(sorted(Counter(e['row'] for e in entries).items())))
