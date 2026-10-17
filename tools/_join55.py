"""Finding 55 final join: classify every FAR operand by WHY it is/isn't relocated.

Inputs:
  analysis/ida_falconcd/farops_export55.json   (IDA: ea, seg, off, dst, fn)
  analysis/ida_falconcd/classification.json    (registered fns)
  game/FALCONCD.EXE                           (RTLink directory + fixup tables)

Bucket order for an operand whose dst does NOT resolve:
  1. FIXUP_LISTED_KEPT      rel present in the record's raw fixup table AND
                            kept by validate_fixup_semantics (seg == w0)
  2. FIXUP_LISTED_DROPPED   rel present in the raw table but seg != w0
                            (dropped by the filter in validate_fixup_semantics.py)
  3. FIXUP_NOT_LISTED       rel absent from the raw table entirely
  4. +0x10000_UNFIXABLE     none of the above makes dst resolve either
and for dst already resolving: ALREADY_OK.

Usage: venv\\Scripts\\python tools\\_join55.py
"""
import json
import struct
from bisect import bisect_right
from collections import Counter

d = open("game/FALCONCD.EXE", "rb").read()
DIR = 0x1E24F
far = json.load(open("analysis/ida_falconcd/farops_export55.json"))
cls = json.load(open("analysis/ida_falconcd/classification.json"))
place = {p["idx"]: p for p in json.load(open("analysis/ida_falconcd/overlay_placement.json"))}
kept_json = {int(k): v for k, v in json.load(
    open("analysis/ida_falconcd/fixups_to_apply.json")).items()}

starts = sorted(v["ea"] for v in cls.values())
ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k) for k, v in cls.items())


def res(ea):
    i = bisect_right(starts, ea) - 1
    if i >= 0 and ivs[i][0] <= ea < ivs[i][1]:
        return ivs[i][2], ivs[i][0] == ea
    return None, False


# raw fixup `off` sets per record, split by whether validate_fixup_semantics kept them
raw_offs, kept_offs, dropped_offs = {}, {}, {}
for idx in range(70):
    oo = DIR + idx * 18
    w0, _w1, w2, _w3, _w4, nfx, _w6, _w7, _w8 = struct.unpack_from("<9H", d, oo)
    if 50 <= idx <= 68:
        tpos = 0xFFFA0 + (w2 << 4)
    elif idx == 69:
        tpos = 0xFFFA0 + (w2 << 4) + 0x60
    elif w2 >= 0x1000:
        tpos = w2 << 4
    else:
        continue
    if tpos + nfx * 4 > len(d):
        continue
    R, K = set(), set()
    for k in range(nfx):
        a, b = struct.unpack_from("<HH", d, tpos + k * 4)
        R.add(a)
        (K if b == w0 else set()).add(a)
    raw_offs[idx] = R
    kept_offs[idx] = K
    dropped_offs[idx] = R - K

# map an ea to its record (record writes bytes at ida_ea..ida_ea+ida_len)
rec_by_range = sorted((p["ida_ea"], p["ida_ea"] + p["ida_len"], i)
                      for i, p in place.items() if p.get("ida_ea") is not None and p["ida_len"])


def rec_of(ea):
    for lo, hi, i in rec_by_range:
        if lo <= ea < hi:
            return i
    return None


c = Counter()
detail = Counter()
for r in far:
    k, _ = res(r["dst"])
    if k is not None:
        c["ALREADY_OK"] += 1
        continue
    k2, ex2 = res(r["dst"] + 0x10000)
    idx = rec_of(r["fn"])
    rel = r["ea"] + 3 - (place[idx]["ida_ea"] if idx is not None else 0)
    if idx is None:
        c["NO_RECORD(inside fn but no overlay rec)"] += 1
        continue
    if k2 is None:
        c["4_UNFIXABLE_by_plus10000"] += 1
        continue
    cands = {rel, r["ea"] + 4 - place[idx]["ida_ea"]}   # tolerate 0/1 seg-prefix bytes
    R = raw_offs.get(idx, set())
    K = kept_offs.get(idx, set())
    if cands & K:
        c["1_LISTED_AND_KEPT_but_not_applied"] += 1
    elif cands & R:
        c["2_LISTED_DROPPED_by_seg!=w0_filter"] += 1
    else:
        c["3_NOT_IN_FIXUP_TABLE"] += 1
    detail[(idx, place[idx]["seg_name"])] += 1

n = sum(c.values())
print("FAR operands exported from IDA: %d" % len(far))
print("")
print("%-44s %6s %7s" % ("bucket", "n", "%"))
for k, v in c.most_common():
    print("%-44s %6d %6.1f%%" % (k, v, 100.0 * v / n))
print("")

unres = sum(v for k, v in c.items() if not k.startswith("ALREADY_OK"))
print("operands with an unresolvable dst: %d" % unres)
for k in ("1_LISTED_AND_KEPT_but_not_applied", "2_LISTED_DROPPED_by_seg!=w0_filter",
          "3_NOT_IN_FIXUP_TABLE", "4_UNFIXABLE_by_plus10000"):
    if c[k]:
        print("   %-40s %5d  (%.0f%% of unresolvable)"
              % (k, c[k], 100.0 * c[k] / max(1, unres)))
print("")
print("where the 'needs +0x10000' ones live (record: n):")
for (idx, name), v in detail.most_common(12):
    print("   idx=%-3d %-14s %d" % (idx, name, v))
