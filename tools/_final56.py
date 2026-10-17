"""Finding 56 outcome metrics (host side, read-only).

Usage: venv\\Scripts\\python tools\\_final56.py
"""
import json
import struct
from bisect import bisect_right
from collections import Counter
from pathlib import Path

IDA = "analysis/ida_falconcd/"
TR = "analysis/traces/"
cls = json.load(open(IDA + "classification.json"))
refs = json.load(open(IDA + "callgraph_refs.json"))["refs"]
cg = json.load(open(TR + "callgraph_partial.json"))
ent = json.load(open(IDA + "overlay_entries.json"))
fb = json.load(open(IDA + "function_bytes.json"))

starts = sorted(v["ea"] for v in cls.values())
ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k) for k, v in cls.items())


def res(ea):
    i = bisect_right(starts, ea) - 1
    if i >= 0 and ivs[i][0] <= ea < ivs[i][1]:
        return ivs[i][2]
    return None


print("== graph ==")
print("   functions        : %d" % len(cls))
print("   static edges     : %d   (baseline 1,764 -> finding 55 2,280)" % cg["edge_counts"]["static"])
print("   static_unresolved: %d   (baseline 1,257)" % cg["edge_counts"]["static_unresolved"])

# overlay orphans (finding 54 baseline 232/255)
indeg = Counter()
for a, b in cg["edges"]:
    indeg[b] += 1
ovl = [k for k, v in cls.items() if v["overlay"]]
res_orph = [k for k, v in cls.items() if not v["overlay"] and indeg[k] == 0]
ovl_orph = [k for k in ovl if indeg[k] == 0]
print("")
print("== orphans (zero indegree) ==")
print("   overlay     : %d/%d (%.0f%%)   [finding 54 baseline 232/255 = 91%%]"
      % (len(ovl_orph), len(ovl), 100.0 * len(ovl_orph) / len(ovl)))
print("   resident    : %d/%d (%.0f%%)" % (len(res_orph), len(cls) - len(ovl),
                                           100.0 * len(res_orph) / max(1, len(cls) - len(ovl))))

# resident -> overlay crossing edges
cross = {(a, b) for a, b in cg["edges"]
         if a in cls and b in cls
         and not cls[a]["overlay"] and cls[b]["overlay"]}
print("")
print("== RESIDENT -> OVERLAY edges ==")
print("   crossing edges : %d   (finding 55 baseline: 8)" % len(cross))
print("   distinct overlay fns reached from resident: %d" % len({b for _, b in cross}))

# thunk table
LO, S, N = 0x2BD9D, 10, 303
slots = [LO + i * S for i in range(N)]
src3 = {r[0] for r in refs}
into = [r for r in refs if LO <= r[1] <= LO + (N - 1) * S + 10]
print("")
print("== thunk table ==")
by_ea = {v["ea"] for v in fb.values()}
print("   slots registered as own fn : %d/%d" % (sum(1 for s in slots if s in by_ea), N))
print("   refs INTO the table        : %d  unresolved %d"
      % (len(into), sum(1 for r in into if not res(r[1]))))
emit = [s for s in slots if (s + 3) in src3]
print("   slots emitting JMP FAR     : %d/%d" % (len(emit), N))

# the 53 slots that overlay_entries used to miss (0..52 + 95, 99)
MISSING = list(range(53)) + [95, 99]
EXE = Path("game/FALCONCD.EXE").read_bytes()
have_rt = {(e["row"], e["target_linear"]) for e in ent}
now_ok = 0
detail = []
for i in MISSING:
    o = 0x1E99D + i * 10
    off, seg, wid = struct.unpack_from("<HHH", EXE, o + 4)
    tgt = ((0x1000 + seg) << 4) + off
    k = res(tgt)
    if k:
        now_ok += 1
    detail.append((i, tgt, k))
print("")
print("== the 55 slots overlay_entries used to miss ==")
print("   their JMP target now has a function: %d/%d" % (now_ok, len(MISSING)))
for i, t, k in detail[:16]:
    print("      slot #%03d target=0x%-7X -> %s" % (i, t, k or "STILL NO FN"))

# why the rest are not registrable
sk = Counter()
for i, t, k in detail:
    if k:
        continue
    fn = next((v for v in fb.values() if v["ea"] <= t < v["ea"] + max(v["size"], 1)), None)
    seg_ok = any(p.get("ida_ea") is not None and p["ida_len"]
                 and p["ida_ea"] <= t < p["ida_ea"] + p["ida_len"]
                 for p in json.load(open(IDA + "overlay_placement.json")))
    sk["registered" if fn else ("no bytes written there" if not seg_ok else "on bytes, but not a prologue/terminator")] += 1
print("")
print("   breakdown of those still without a function:")
for k, v in sk.most_common():
    print("      %-46s %d" % (k, v))
