"""Solve thunk-word -> record-row assignment under two runtime models.

Model 1 (dir-run packing): rows with same w0 consecutive in dir share an arena at
  base=(0x1000+w0)<<4; within a consecutive run, records pack cumulatively (paras).
Model 2 (all-at-base): every record's block = [base, base+span*16) regardless of run
  (transient records with same w0 all load at arena base -> overlap).

For each thunk word: collect all target linears; a row matches iff every target
falls inside that row's block. Report the assignment matrix.
"""
import struct
from pathlib import Path
from collections import defaultdict

EXE = Path('game/FALCONCD.EXE').read_bytes()
DIR = 0x1E24F
THUNK = 0x1EBAF

rows = []
for i in range(70):
    o = DIR + i * 18
    w0, w1, w2, w3, w4, w5, w6, w7, w8 = struct.unpack_from('<9H', EXE, o)
    rows.append(dict(idx=i, w0=w0, span=w4, idf=w7, fixups=w5))

# blocks, model 1: consecutive-run packing
blocks1 = {}
cur_w0, cur_end = None, None
for r in rows:
    if r['w0'] != cur_w0:
        cur_w0 = r['w0']
        cur_end = (0x1000 + r['w0']) << 4
    start = cur_end
    end = start + r['span'] * 16
    blocks1[r['idx']] = (start, end)
    cur_end = end

# blocks, model 2: all at base
blocks2 = {r['idx']: (((0x1000 + r['w0']) << 4),
                      ((0x1000 + r['w0']) << 4) + r['span'] * 16) for r in rows}

# thunks grouped by word
targets = defaultdict(list)
for i in range(400):
    o = THUNK + i * 10
    if o + 10 > len(EXE) or EXE[o] != 0xE8 or EXE[o + 3] != 0xEA:
        break
    loff, lseg, wid = struct.unpack_from('<HHH', EXE, o + 4)
    lin = ((0x1000 + lseg) << 4) + loff
    targets[wid].append(lin)

print('%-5s %-5s | %-28s | %-28s' % ('word', 'ntg', 'model1 matching rows', 'model2 matching rows'))
fail1 = fail2 = 0
assign = {}
for wid in sorted(targets):
    tg = targets[wid]
    m1 = [r['idx'] for r in rows if all(s <= t < e for s, e in [blocks1[r['idx']]] for t in tg)]
    m2 = [r['idx'] for r in rows if all(blocks2[r['idx']][0] <= t < blocks2[r['idx']][1] for t in tg)]
    if not m1:
        fail1 += 1
    if not m2:
        fail2 += 1
    assign[wid] = (m1, m2)
    print('%-5d %-5d | %-28s | %-28s' % (wid, len(tg), m1 if m1 else 'NO MATCH', m2 if m2 else 'NO MATCH'))

print('words with no model1 match: %d / %d' % (fail1, len(targets)))
print('words with no model2 match: %d / %d' % (fail2, len(targets)))

# uniqueness stats
u1 = sum(1 for w, (a, b) in assign.items() if len(a) == 1)
u2 = sum(1 for w, (a, b) in assign.items() if len(b) == 1)
print('unique assignment: model1=%d model2=%d of %d' % (u1, u2, len(assign)))

# what would word=index and word=id-field give?
idx_ok = idf_ok = 0
for wid, (m1, m2) in assign.items():
    if wid in m1:
        idx_ok += 1
    if (wid - 2) in m1:
        idf_ok += 1
print('model1: word==row-index matches %d, word==id-field(row=wid-2) matches %d' % (idx_ok, idf_ok))
