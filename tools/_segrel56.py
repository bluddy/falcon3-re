"""Finding 56: is a fixup's absolute record offset `off`, or `(seg - w0)*16 + off`?

The RTLink fixup pair is (off, seg) with seg a paragraph inside the record's
arena [w0, w0+span).  Finding 55 measured R05_1E10's far-operands aligning at
a +0x1540-byte shift -- and 0x1540 = (0x1F64 - 0x1E10)*16 where 0x1F64 is the
MOST COMMON `seg` in that very table (1442 of 3529).

Hypothesis: the pair's `seg` names the paragraph the fixup belongs to, so
    absolute_offset = (seg - w0) * 16 + off
which degenerates to plain `off` when seg == w0 (which is why the records
finding 55 called "well-aligned" -- 27, 30, 1 -- look fine: their top seg IS w0).

Score both formulas by: does the resulting address fall exactly on a direct
FAR (9A/EA) segment word?

Usage: venv\\Scripts\\python tools\\_segrel56.py
"""
import json
import struct
from pathlib import Path

EXE = Path("game/FALCONCD.EXE").read_bytes()
DIR = 0x1E24F
place = {p["idx"]: p for p in json.load(open("analysis/ida_falconcd/overlay_placement.json"))}

print("%-4s %-13s %6s %8s %8s %10s %10s   %s"
      % ("idx", "seg_name", "nfx", "A=off", "B=segrel", "farwords", "A/word", "B/word"))
tot_a = tot_b = 0
for idx in sorted(place):
    p = place[idx]
    if p["addr"] == "skip" or not p["data_file"] or not p["ida_len"]:
        continue
    o = DIR + idx * 18
    w0, _, w2, _, span, nfx, _, _, _ = struct.unpack_from("<9H", EXE, o)
    if 50 <= idx <= 68:
        tpos = 0xFFFA0 + (w2 << 4)
    elif idx == 69:
        tpos = 0xFFFA0 + (w2 << 4) + 0x60
    elif w2 >= 0x1000:
        tpos = w2 << 4
    else:
        continue
    if tpos + nfx * 4 > len(EXE):
        continue

    blob = EXE[p["data_file"]:p["data_file"] + p["ida_len"]]
    far = set()
    i = 0
    while i < len(blob) - 5:
        if blob[i] in (0x9A, 0xEA):
            far.add(i + 3)
            i += 5
        else:
            i += 1
    if not far:
        continue

    a = b = 0
    for k in range(nfx):
        off, seg = struct.unpack_from("<HH", EXE, tpos + k * 4)
        if 0 <= off < len(blob) and off in far:
            a += 1
        rel = (seg - w0) * 16 + off
        if 0 <= rel < len(blob) and rel in far:
            b += 1
    tot_a += a
    tot_b += b
    note = ""
    if b > a and nfx > 50:
        note = "  <-- segrel wins"
    elif a > b and nfx > 50:
        note = "  <-- plain off wins"
    print("%-4d %-13s %6d %8d %8d %10d %9.1f%% %9.1f%%%s"
          % (idx, p["seg_name"], nfx, a, b, len(far),
             100.0 * a / len(far), 100.0 * b / len(far), note))

print("")
print("TOTAL  A (plain off) = %d   B ((seg-w0)*16 + off) = %d" % (tot_a, tot_b))

# record 5 detail: what seg do the far-matching pairs carry?
p = place[5]
_w0, _, w2, _, _sp, nfx, _, _, _ = struct.unpack_from("<9H", EXE, DIR + 5 * 18)
tpos = w2 << 4
blob = EXE[p["data_file"]:p["data_file"] + p["ida_len"]]
far = set()
i = 0
while i < len(blob) - 5:
    if blob[i] in (0x9A, 0xEA):
        far.add(i + 3)
        i += 5
    else:
        i += 1
from collections import Counter
seg_of_B_matches = Counter()
seg_of_A_matches = Counter()
for k in range(nfx):
    off, seg = struct.unpack_from("<HH", EXE, tpos + k * 4)
    if off in far:
        seg_of_A_matches[seg] += 1
    rel = (seg - 0x1E10) * 16 + off
    if 0 <= rel < len(blob) and rel in far:
        seg_of_B_matches[seg] += 1
print("")
print("R05_1E10: seg values of pairs that land on a far segword")
print("  formula A (plain off)      :", [(hex(s), n) for s, n in seg_of_A_matches.most_common(6)])
print("  formula B (seg-relative)   :", [(hex(s), n) for s, n in seg_of_B_matches.most_common(6)])
