"""Finding 57 -- host-side sizing of the sub-block fixup pass (read-only).

Formula under test:  abs_off = (seg - w0) * 16 + off      [paragraph anchor]
Filters:             seg inside the record's arena, abs_off inside the written
                     window, and the patched word must look like a link-time
                     paragraph (word + 0x1000 lands in a segment we wrote).

Reports: how many entries are new vs already applied by pass 1, which functions
would change, and how many of the 446 dead far calls become reachable.

Usage: venv\\Scripts\\python tools\\_size57.py
"""
import json
import struct
from bisect import bisect_right
from collections import Counter, defaultdict
from pathlib import Path

EXE = Path("game/FALCONCD.EXE").read_bytes()
DIR = 0x1E24F
IDA = "analysis/ida_falconcd/"

place = {p["idx"]: p for p in json.load(open(IDA + "overlay_placement.json"))}
# pass-1 file stores [[rel, word_before], ...]; index it by rel only
old_applied = {int(k): {tuple(x)[0] for x in v} for k, v in
               json.load(open(IDA + "fixups_to_apply.json")).items()}
fb = json.load(open(IDA + "function_bytes.json"))
far = json.load(open(IDA + "farops_export55.json"))
cls = json.load(open(IDA + "classification.json"))

# every linear range the IDB has bytes in
WIN = [(0x10000, 0x2CF60, "resident")]
for p in place.values():
    if p.get("ida_ea") is not None and p["ida_len"]:
        WIN.append((p["ida_ea"], p["ida_ea"] + p["ida_len"], p["seg_name"]))


def para_ok(word):
    if word > 0xFFFF:
        return False
    lin = ((word + 0x1000) & 0xFFFF) << 4
    return any(lo <= lin < hi for lo, hi, _ in WIN)


# function index for "which function owns this ea"
ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k, v["size"]) for k, v in fb.items())
fstarts = [a for a, _, _, _ in ivs]


def owner(ea):
    i = bisect_right(fstarts, ea) - 1
    if i >= 0 and ivs[i][0] <= ea < ivs[i][1]:
        return ivs[i][2], ivs[i][0], ivs[i][3]
    return None, None, None


SPECIAL = {0x1D0D, 0x1D31}
tot = Counter()
per_rec = {}
patch_set = defaultdict(list)     # idx -> [(abs_off, w_before, ea)]

for idx in sorted(place):
    p = place[idx]
    if p.get("addr") == "skip" or not p.get("data_file") or not p.get("ida_len"):
        continue
    o = DIR + idx * 18
    if o + 18 > len(EXE):
        continue
    w0, _w1, w2, _w3, span, nfx, _w6, _idf, _ds = struct.unpack_from("<9H", EXE, o)
    if idx == 69:
        tpos = 0xFFFA0 + (w2 << 4) + 0x60
    elif 50 <= idx <= 68:
        tpos = 0xFFFA0 + (w2 << 4)
    elif w2 >= 0x1000:
        tpos = w2 << 4
    else:
        tot["no_table_pos"] += 1
        continue
    if tpos + nfx * 4 > len(EXE):
        tot["table_oob"] += 1
        continue
    arena = set(range(w0, w0 + max(1, span))) | SPECIAL
    pr = Counter()
    for k in range(nfx):
        off, seg = struct.unpack_from("<HH", EXE, tpos + k * 4)
        tot["pairs"] += 1
        if seg not in arena:
            pr["dropped_seg_out_of_arena"] += 1
            continue
        abs_off = (seg - w0) * 16 + off
        if not (0 <= abs_off + 2 <= p["ida_len"]):
            pr["dropped_abs_off_outside_window"] += 1
            continue
        fpos = p["data_file"] + abs_off
        if fpos + 2 > len(EXE):
            pr["dropped_file_oob"] += 1
            continue
        w = struct.unpack_from("<H", EXE, fpos)[0]
        pr["in_window"] += 1
        if not para_ok(w):
            pr["dropped_word_not_link_para"] += 1
            continue
        pr["word_ok"] += 1
        ea = p["ida_ea"] + abs_off
        already = abs_off in old_applied.get(idx, set())
        if already:
            pr["already_applied_pass1"] += 1
        else:
            pr["NEW"] += 1
            patch_set[idx].append((abs_off, w, ea))
    per_rec[idx] = (p["seg_name"], pr)

print("%-5s %-14s %6s %6s %6s %7s %7s %7s %7s" %
      ("idx", "seg", "pairs", "inwin", "wordok", "pass1", "NEW", "no-para", "oow"))
for idx, (name, pr) in sorted(per_rec.items()):
    if pr.get("NEW") or pr.get("dropped_word_not_link_para", 0) > 50:
        print("%-5d %-14s %6d %6d %6d %7d %7d %7d %7d"
              % (idx, name, pr.get("in_window", 0) + pr.get("dropped_seg_out_of_arena", 0)
              + pr.get("dropped_abs_off_outside_window", 0)
              + pr.get("dropped_file_oob", 0), pr.get("in_window", 0),
                 pr.get("word_ok", 0), pr.get("already_applied_pass1", 0),
                 pr.get("NEW", 0), pr.get("dropped_word_not_link_para", 0),
                 pr.get("dropped_abs_off_outside_window", 0)))

print("")
for k in ("pairs", "dropped_seg_out_of_arena", "dropped_abs_off_outside_window",
          "dropped_file_oob", "in_window", "word_ok", "dropped_word_not_link_para",
          "already_applied_pass1", "NEW"):
    if tot[k]:
        print("  %-38s %7d" % (k, tot[k]))

# ---- which functions change ----
funcs = Counter()
for idx, items in patch_set.items():
    for abs_off, w, ea in items:
        k, fea, fsz = owner(ea)
        if k:
            funcs[k] += 1
        else:
            funcs["<no owning function>"] += 1
print("")
print("functions receiving >=1 patch: %d" % len(funcs))
print("  top 12:", funcs.most_common(12))

# ---- how many of the dead far calls does this fix? ----
rec_of_fn = {}
for p in place.values():
    if p.get("ida_ea") is not None and p["ida_len"]:
        rec_of_fn[(p["ida_ea"], p["ida_ea"] + p["ida_len"])] = p["idx"]
valid = {(i, a) for i, items in patch_set.items() for a, _, _ in items}
# also count pass-1 entries as available (already correct)
for i, s in old_applied.items():
    for a in s:
        valid.add((i, a))

starts = [x[0] for x in ivs]


def res2(ea):
    i = bisect_right(starts, ea) - 1
    if i >= 0 and ivs[i][0] <= ea < ivs[i][1]:
        return ivs[i][2]
    return None


fixable = [r for r in far if res2(r["dst"]) is None and res2(r["dst"] + 0x10000)]
covered = 0
for r in fixable:
    idx = None
    for (lo, hi), i in rec_of_fn.items():
        if lo <= r["fn"] < hi:
            idx = i
            break
    if idx is None:
        continue
    ea_ida = place[idx]["ida_ea"]
    # seg word sits at insn head +3 (or +4 with a prefix) -- accept either
    for cand in (r["ea"] + 3, r["ea"] + 4):
        if (idx, cand - ea_ida) in valid:
            covered += 1
            break
print("")
print("dead far calls (dst unresolvable, dst+0x10000 resolves): %d" % len(fixable))
print("   ...whose segment word IS covered by a valid fixup entry: %d" % covered)
print("   ...not covered (would stay dead): %d" % (len(fixable) - covered))
