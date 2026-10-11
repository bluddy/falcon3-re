"""Validate RTLink fixup semantics host-side before applying to the IDB.

Hypothesis (finding 17/18 + gunship note "runtime = link + L"):
  each fixup pair (off, seg) with seg == record's w0 locates a word at
  record-relative `off`; loader does word += L (L = 0x1000 in IDA space).

Check: the BEFORE word should be a plausible LINK-time paragraph
(resident 0x0084..0x1CF5 or overlay w0s 0x1CF6..0x606E), AFTER = +0x1000.
Also count pairs whose seg != w0 (cross-arena, skipped by design).
"""
import json
import struct
from collections import Counter
from pathlib import Path

EXE = Path('game/FALCONCD.EXE').read_bytes()
DIR = 0x1E24F

rows = {}
for i in range(70):
    o = DIR + i * 18
    w0, w1, w2, w3, w4, w5, w6, w7, w8 = struct.unpack_from('<9H', EXE, o)
    rows[i] = dict(idx=i, w0=w0, w2=w2, span=w4, fixups=w5)

placements = {p['idx']: p for p in json.load(open('analysis/ida_falconcd/overlay_placement.json'))}
located = {e['idx']: e for e in json.load(open('analysis/ida_falconcd/record_fixup_located.json'))}

LINK_OK = set(range(0x0084, 0x1CF6)) | {0x1CF6, 0x1D0D, 0x1D31, 0x1E10, 0x569F,
                                        0x5CD9, 0x5DFF, 0x5E0B, 0x5E8F, 0x5F6C, 0x606E}

CLUSTER_B0 = 0xFFFA0


def table_pos(r):
    # cluster B (rows 50-69): found 2026-10-11 (finding 20)
    if 50 <= r['idx'] <= 68:
        return CLUSTER_B0 + (r['w2'] << 4)
    if r['idx'] == 69:
        return CLUSTER_B0 + (r['w2'] << 4) + 0x60
    e = located.get(r['idx'])
    if r['fixups'] and r['w2'] >= 0x1000:
        ov = set(range(r['w0'], r['w0'] + max(1, r['span']))) | {0x1D0D, 0x1D31}
        bp = r['w2'] << 4
        ok = sum(1 for k in range(r['fixups'])
                 if struct.unpack_from('<H', EXE, bp + k * 4 + 2)[0] in ov) / r['fixups']
        if ok >= 0.8:
            return bp
    if e and e['fixup_frac'] >= 0.8:
        return e['fixup_pos']
    if r['w2'] >= 0x1000:
        return r['w2'] << 4
    return None


before_hist = Counter()
after_hist = Counter()
bad = 0
cross = 0
total = 0
pairs_out = {}

for idx, r in rows.items():
    p = placements.get(idx)
    if not p or p['addr'] == 'skip' or not p['data_file']:
        continue
    pos = table_pos(r)
    if pos is None or pos + r['fixups'] * 4 > len(EXE):
        continue
    plist = []
    for k in range(r['fixups']):
        off, seg = struct.unpack_from('<HH', EXE, pos + k * 4)
        if seg != r['w0']:
            cross += 1
            continue
        if off + 2 > p['span_bytes']:
            bad += 1
            continue
        fpos = p['data_file'] + off
        if fpos + 2 > len(EXE):
            bad += 1
            continue
        w = struct.unpack_from('<H', EXE, fpos)[0]
        total += 1
        before_hist[w] += 1
        after_hist[(w + 0x1000) & 0xFFFF] += 1
        plist.append((off, w))
    if plist:
        pairs_out[idx] = plist

print('fixups validated: %d in-seg (cross-seg skipped: %d, bad: %d)' % (total, cross, bad))
print()
print('BEFORE word: plausible-link-paragraph fraction = %.3f' % (
    sum(n for w, n in before_hist.items() if w in LINK_OK) / max(1, total)))
print('top BEFORE words:', [(hex(w), n) for w, n in before_hist.most_common(12)])
print('top AFTER  words:', [(hex(w), n) for w, n in after_hist.most_common(12)])
# how many before-words look like segments at all (>=0x40, <0x10000, aligned?)
seglike = sum(n for w, n in before_hist.items() if 0x40 <= w < 0x7000)
print('before words >=0x40 and <0x7000: %.3f' % (seglike / max(1, total)))

json.dump({str(k): v for k, v in pairs_out.items()},
          open('analysis/ida_falconcd/fixups_to_apply.json', 'w'))
print('wrote analysis/ida_falconcd/fixups_to_apply.json (%d records)' % len(pairs_out))
