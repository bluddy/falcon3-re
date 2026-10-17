"""Bucket the static refs whose SOURCE resolves to a registered function but
whose DESTINATION does not (`callgraph_refs.json`), and control-test the
"+0x10000" (image-load-paragraph) relocation hypothesis.

Finding 55.

Usage: venv\\Scripts\\python tools\\unresolved_dsts55.py
"""
import json
import random
from bisect import bisect_right
from collections import Counter

IDA = "analysis/ida_falconcd/"
cls = json.load(open(IDA + "classification.json"))
refs = json.load(open(IDA + "callgraph_refs.json"))["refs"]
place = json.load(open(IDA + "overlay_placement.json"))

starts = sorted(v["ea"] for v in cls.values())
ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k) for k, v in cls.items())
starts_set = {iv[0] for iv in ivs}


def resolve(ea):
    i = bisect_right(starts, ea) - 1
    if i >= 0 and ivs[i][0] <= ea < ivs[i][1]:
        return ivs[i][2]
    return None


THUNK_LO, THUNK_HI = 0x2BD9D, 0x2C973
OVL_LO, OVL_HI = 0x2CF60, 0x100000
ovl_ranges = sorted(
    (p["ida_ea"], p["ida_ea"] + p["ida_len"], p["seg_name"])
    for p in place if p.get("ida_ea") is not None and p.get("ida_len"))


def ovl_seg(ea):
    for lo, hi, n in ovl_ranges:
        if lo <= ea < hi:
            return n
    return None


unres = [(s, d) for s, d, _ in refs if resolve(s) and not resolve(d)]
print("static refs: %d ; src-resolves & dst-does-not: %d ; distinct dst: %d"
      % (len(refs), len(unres), len({d for _, d in unres})))

DELTA = [("+10000", 0x10000), ("-10000", -0x10000), ("+1000", 0x1000),
         ("-1000", -0x1000), ("+E5E0", 0xE5E0), ("-E5E0", -0xE5E0),
         ("+E0B0", 0xE0B0), ("-E0B0", -0xE0B0), ("+E5E", 0xE5E),
         ("-E5E", -0xE5E), ("+E0B", 0xE0B), ("-E0B", -0xE0B)]

# per-ref bucket: src region x dst category
cat = Counter()
for s, d in unres:
    src = "R*" if cls[resolve(s)]["overlay"] else "Res"
    if THUNK_LO <= d <= THUNK_HI:
        c = "A_in_thunk_table"
    elif OVL_LO <= d < OVL_HI or d >= 0x100000:
        c = ("B_in_%s_no_fn" % ovl_seg(d)) if ovl_seg(d) else "B_in_overlay_no_seg"
    elif d < 0x10000:
        c = "C_below_image"
    elif d < OVL_LO:
        c = "D_resident_unregistered"
    else:
        c = "E_other"
    if c.startswith(("A_", "B_", "C_", "D_")):
        hits = [n for n, dl in DELTA
                if 0x10000 <= d + dl < 0x400000 and resolve(d + dl)]
        if hits:
            c += "|shift_%s%s" % (hits[0], "_EXACT" if d + dict(DELTA)[hits[0]] in starts_set else "")
    cat[(src, c)] += 1

print("")
print("%-6s %-46s %6s" % ("src", "dst category", "n"))
for (r, c), n in sorted(cat.items(), key=lambda x: -x[1]):
    print("%-6s %-46s %d" % (r, c, n))
print("bucketed: %d" % sum(cat.values()))

# fourth category: dst is a low target_linear whose function lives at the high
# entry_ea of the R*_s synthetic copy (finding 54's remap candidate)
ent = json.load(open(IDA + "overlay_entries.json"))
tl2ee = {}
for e in ent:
    if e["target_linear"] != e["entry_ea"]:
        tl2ee.setdefault(e["target_linear"], e["entry_ea"])
tl_refs = [(s, d) for s, d in unres if d in tl2ee]
print("")
print("dst is a target_linear with a distinct entry_ea: %d refs "
      "(of which resolve after target_linear->entry_ea remap: %d)"
      % (len(tl_refs), sum(1 for _, d in tl_refs if resolve(tl2ee[d]))))

# ---- CONTROL: does "+0x10000 lands on a function start" beat a random base? ----
dsts = sorted({d for _, d in unres})
real = Counter()
for d in dsts:
    for n, dl in DELTA:
        if 0x10000 <= d + dl < 0x400000 and (d + dl) in starts_set:
            real[n] += 1
            break
random.seed(7)
ctrl = Counter()
for d in dsts:
    base = random.randint(0x10000, 0x1B0000)
    for n, dl in DELTA:
        if 0x10000 <= base + dl < 0x400000 and (base + dl) in starts_set:
            ctrl[n] += 1
            break
print("")
print("delta landing EXACT on a registered function start (first match wins)")
print("%10s %8s %8s" % ("delta", "real", "CONTROL"))
for n, dl in DELTA:
    if real[n] or ctrl[n]:
        print("%10s %8d %8d" % (n, real[n], ctrl[n]))
print("totals: real=%d control=%d (n=%d dsts each)"
      % (sum(real.values()), sum(ctrl.values()), len(dsts)))
