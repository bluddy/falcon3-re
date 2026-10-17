"""Finding 58 pre-pass (host, read-only): collect every static ref destination
that lies outside any registered function, keyed by address.

Writes analysis/ida_falconcd/dst_list.json:
  [{"ea", "n", "call", "jmp", "zone", "srcs"}, ...] sorted by descending refs
where zone is overlay:<seg> / thunk / resident.

These are the addresses the audit (tools/audit_dsts.py) will decode in IDA.

Usage: venv\\Scripts\\python tools\\dst_list.py
"""
import json
from bisect import bisect_right
from collections import Counter, defaultdict
from pathlib import Path

IDA = Path("analysis/ida_falconcd")
cls = json.loads((IDA / "classification.json").read_text())
refs = json.loads((IDA / "callgraph_refs.json").read_text())["refs"]
place = json.loads((IDA / "overlay_placement.json").read_text())

ivs = sorted((v["ea"], v["ea"] + max(v["size"], 1), k) for k, v in cls.items())
starts = [x[0] for x in ivs]


def res(ea):
    i = bisect_right(starts, ea) - 1
    return ivs[i][2] if i >= 0 and ivs[i][0] <= ea < ivs[i][1] else None


ovl = [(p["ida_ea"], p["ida_ea"] + p["ida_len"], p["seg_name"])
       for p in place if p.get("ida_ea") is not None and p["ida_len"]]


def zone(ea):
    for lo, hi, nm in ovl:
        if lo <= ea < hi:
            return "overlay:" + nm
    if 0x2BD9D <= ea < 0x2C973:
        return "thunk"
    return "resident"


buckets = defaultdict(list)
for s, d, c in refs:
    if res(d) is None:
        buckets[d].append((s, c))

rows = [{"ea": ea,
         "n": len(v),
         "call": sum(1 for _, c in v if c),
         "jmp": sum(1 for _, c in v if not c),
         "zone": zone(ea),
         "srcs": sorted({s for s, _ in v})}
        for ea, v in buckets.items()]
rows.sort(key=lambda r: (-r["n"], r["ea"]))
(IDA / "dst_list.json").write_text(json.dumps(rows))

print("unresolved refs: %d   distinct dsts: %d"
      % (sum(r["n"] for r in rows), len(rows)))
print("by zone:", dict(Counter(r["zone"].split(":")[0] for r in rows)))
for lo, hi, nm in ((0x2E2F0, 0x3ACAC, "inside sub_2E2F0"),
                   (0x3ACAC, 0x669F0, "R05 upper half 0x3ACAC..0x669F0")):
    hit = [r for r in rows if lo <= r["ea"] < hi]
    print("%-26s : %3d dsts / %4d refs" % (nm, len(hit), sum(r["n"] for r in hit)))
print("\ntop 25 by ref count:")
for r in rows[:25]:
    print("   0x%-7X n=%-4d call=%-4d jmp=%-4d %s"
          % (r["ea"], r["n"], r["call"], r["n"] - r["call"], r["zone"]))
