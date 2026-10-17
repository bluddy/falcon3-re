"""Finding 60 step P0 (host, read-only): inventory the R05 upper half
0x3ACAC..0x669F0, block by block, before any registration.

For each of the 18 anchor-delimited blocks reports: size, byte content
(printable string runs, printable fraction, head bytes), the unresolved call
destinations inside it (dsts/refs/strong-entry), RTLink `entry_ea`s that land
there, and the functions already registered in it.  Also derives candidate
data holes from merged string runs so P3 can sha256-pin them the way finding
59 pinned the blob's three.

Bytes come from FALCONCD.EXE through overlay_placement's data_file mapping
(the same mapping validated against function_bytes in finding 57).

Writes analysis/ida_falconcd/upper_map.json.

Usage: venv\\Scripts\\python tools\\map_upper.py
"""
import json
from pathlib import Path

EXE = Path("game/FALCONCD.EXE").read_bytes()
IDA = Path("analysis/ida_falconcd")
LO, HI = 0x3ACAC, 0x669F0

place = json.loads((IDA / "overlay_placement.json").read_text())
amap = json.loads((IDA / "sub2e2f0_map.json").read_text())
cls = json.loads((IDA / "classification.json").read_text())
lst = json.loads((IDA / "dst_list.json").read_text())
aud = {r["ea"]: r for r in json.loads((IDA / "dst_audit.json").read_text())["targets"]}
entries = json.loads((IDA / "overlay_entries.json").read_text())

rec = next(p for p in place if p.get("ida_ea") is not None and p["ida_len"]
           and p["ida_ea"] <= LO < p["ida_ea"] + p["ida_len"])
blob = EXE[rec["data_file"] + (LO - rec["ida_ea"]): rec["data_file"] + (HI - rec["ida_ea"])]
assert len(blob) == HI - LO, len(blob)

anchors = sorted(int(k, 16) for k in amap["anchors"] if LO <= int(k, 16) < HI)
pts = [LO] + anchors + [HI]

dsts = [r for r in lst if LO <= r["ea"] < HI]
fns = [(v["ea"], v["ea"] + v["size"], k) for k, v in cls.items()
       if v.get("ea") is not None and LO <= v["ea"] < HI]


def runs_of(chunk, base):
    out, i = [], 0
    while i < len(chunk):
        if 0x20 <= chunk[i] < 0x7F:
            j = i
            while j < len(chunk) and 0x20 <= chunk[j] < 0x7F:
                j += 1
            if j - i >= 6 and (j == len(chunk) or chunk[j] == 0):
                out.append((base + i, j - i, chunk[i:j].decode("ascii")))
                i = j
                continue
        i += 1
    return out


blocks = []
all_runs = {}
for a, b in zip(pts, pts[1:]):
    chunk = blob[a - LO:b - LO]
    runs = runs_of(chunk, a)
    all_runs[a] = runs
    printable = sum(1 for x in chunk if 0x20 <= x < 0x7F or x == 0)
    head = chunk[:16]
    hd = sum(1 for x in head if 0x20 <= x < 0x7F or x == 0)
    bdst = [r for r in dsts if a <= r["ea"] < b]
    bent = [e["entry_ea"] for e in entries
            if e.get("entry_ea") and a <= e["entry_ea"] < b]
    bfn = [(s, e, k) for s, e, k in fns if a <= s < b]
    blocks.append({
        "lo": a, "hi": b, "size": b - a,
        "printable_frac": round(printable / max(1, len(chunk)), 3),
        "head_hex": head.hex(),
        "head_ascii": "".join(chr(x) if 0x20 <= x < 0x7F else "." for x in head),
        "head_data": hd >= 8,
        "strings": [{"ea": ea, "len": n, "text": t} for ea, n, t in runs[:8]],
        "n_strings": len(runs),
        "dsts": len(bdst), "refs": sum(r["n"] for r in bdst),
        "strong": sum(1 for r in bdst if aud[r["ea"]].get("prev_is_term")),
        "rtlink_entries": sorted(bent),
        "functions": [{"key": k, "ea": s, "size": e - s} for s, e, k in sorted(bfn)],
        "covered_bytes": sum(e - s for s, e, _k in bfn),
        "dst_eas": sorted(r["ea"] for r in bdst),
    })

# candidate holes: merged string clusters (+ data-led heads up to the first dst)
holes = []
for blk in blocks:
    rs = all_runs.get(blk["lo"], [])
    if not rs:
        continue
    runs = [(lo2, lo2 + n) for lo2, n, _t in rs]
    merged = []
    for lo, hi in runs:
        if merged and lo - merged[-1][1] <= 64:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    for lo, hi in merged:
        holes.append({"lo": lo, "hi": hi, "size": hi - lo,
                      "block": "0x%X..0x%X" % (blk["lo"], blk["hi"]),
                      "why": "; ".join(t for lo2, n, t in rs
                                       if lo <= lo2 < hi)[:120]})

zero = [b for b in blocks if b["dsts"] == 0]
rich = sorted(blocks, key=lambda b: -b["refs"])[:5]
print("== R05 upper half 0x%X..0x%X : %d B ==" % (LO, HI, HI - LO))
print("   blocks (anchor-delimited) : %d" % len(blocks))
print("   functions registered      : %d covering %d B (%.1f%%)"
      % (len(fns), sum(b["covered_bytes"] for b in blocks),
         100.0 * sum(b["covered_bytes"] for b in blocks) / (HI - LO)))
print("   unresolved dsts here      : %d (%d refs)   RTLink entry_ea: %d"
      % (len(dsts), sum(r["n"] for r in dsts),
         sum(len(b["rtlink_entries"]) for b in blocks)))
print("   string runs               : %d  -> %d candidate holes / %d B"
      % (sum(b["n_strings"] for b in blocks), len(holes),
         sum(h["size"] for h in holes)))
print("\n   %-16s %-7s %-5s %-5s %-6s %-7s %s"
      % ("block", "size", "dsts", "refs", "strong", "rtlink", "fns/strings"))
for b in blocks:
    print("   0x%-6X..%-6X %7d %5d %5d %6d %6d   %d fns, %d strings%s"
          % (b["lo"], b["hi"], b["size"], b["dsts"], b["refs"], b["strong"],
             len(b["rtlink_entries"]), len(b["functions"]), b["n_strings"],
             "  [DATA-HEAD]" if b["head_data"] else ""))
print("\n   zero call evidence: %s"
      % ", ".join("0x%X..0x%X (%d B)" % (b["lo"], b["hi"], b["size"]) for b in zero))
print("   richest: %s" % ", ".join("0x%X (%d refs)" % (b["lo"], b["refs"]) for b in rich))
print("   RTLink entry_ea in range: %s"
      % ", ".join("0x%X" % e for b in blocks for e in b["rtlink_entries"]))

json.dump({"range": [LO, HI], "blocks": blocks, "holes": holes,
           "functions": [{"key": k, "ea": s, "size": e - s} for s, e, k in sorted(fns)],
           "dst_total": len(dsts), "ref_total": sum(r["n"] for r in dsts)},
          open(IDA / "upper_map.json", "w"))
print("\nwrote analysis/ida_falconcd/upper_map.json")
