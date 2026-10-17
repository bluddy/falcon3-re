"""Account for every one of the 303 .RTLink thunk slots after the 0x1E99D fix.

Why is each slot absent from overlay_entries.json?

Usage: venv\\Scripts\\python tools\\_slots56.py
"""
import json
import struct
from pathlib import Path

EXE = Path("game/FALCONCD.EXE").read_bytes()
THUNK = 0x1E99D
placements = {p["idx"]: p for p in json.load(open("analysis/ida_falconcd/overlay_placement.json"))}
ent = json.load(open("analysis/ida_falconcd/overlay_entries.json"))

have = {(e["row"], e["target_linear"], e["entry_ea"]) for e in ent}
have_row_target = {(e["row"], e["target_linear"]) for e in ent}

slots = []
for i in range(400):
    o = THUNK + i * 10
    if o + 10 > len(EXE) or EXE[o] != 0xE8 or EXE[o + 3] != 0xEA:
        break
    loff, lseg, wid = struct.unpack_from("<HHH", EXE, o + 4)
    slots.append((i, wid, loff, lseg))

print("slots parsed: %d" % len(slots))
print("overlay_entries rows: %d" % len(ent))

from collections import Counter
reasons = Counter()
detail = []
seen = set()
for i, wid, loff, lseg in slots:
    target = ((0x1000 + lseg) << 4) + loff
    p = placements.get(wid)
    if (wid, target) in have_row_target:
        reasons["PRESENT"] += 1
        continue
    if not p or p["addr"] == "skip" or not p["ida_len"]:
        reasons["D1_placement_skip_or_nolen"] += 1
        detail.append((i, wid, hex(target), "placement %s / ida_len=%s"
                       % (p["addr"] if p else "NONE", p["ida_len"] if p else "-")))
        continue
    rel = target - p["real_ea"]
    if rel < 0:
        reasons["D2_rel_negative"] += 1
        detail.append((i, wid, hex(target), "rel=%d (real_ea=0x%X span=%d)"
                       % (rel, p["real_ea"], p["span_bytes"])))
        continue
    entry = p["ida_ea"] + rel
    key = (wid, entry)
    if key in seen:
        reasons["D3_duplicate(wid,entry)"] += 1
        detail.append((i, wid, hex(target), "entry=0x%X duplicate" % entry))
        continue
    seen.add(key)
    if rel >= p["ida_len"]:
        reasons["D4_out_of_bounds(rel>=ida_len)"] += 1
        detail.append((i, wid, hex(target),
                       "entry=0x%X rel=%d >= ida_len=%d (record 0x%X..0x%X)"
                       % (entry, rel, p["ida_len"], p["ida_ea"],
                          p["ida_ea"] + p["ida_len"])))
        continue
    reasons["D5_other"] += 1
    detail.append((i, wid, hex(target), "entry=0x%X fell through" % entry))

print("")
for k, v in reasons.most_common():
    print("  %-34s %d" % (k, v))
print("")
print("absent slots and why:")
for i, wid, tgt, why in detail:
    print("   slot #%03d rec=%-3d target=%-9s %s" % (i, wid, tgt, why))
