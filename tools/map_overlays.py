#!/usr/bin/env python3
"""Finding 64 (host, read-only): compute candidate data holes for the 6 top
R* overlay segments, the same way map_upper.py does for the R05 upper half.

Reads bytes from FALCONCD.EXE via overlay_placement.json.  For each overlay
range, finds merged printable string runs (>=6, NUL/space terminated) and
data-led heads, emits holes with live sha256 so the REGISTER gate can pin
them.  Writes analysis/ida_falconcd/overlay_map.json (same schema as
upper_map.json: range/blocks/holes/functions/dst_total/ref_total).

Usage: venv\\Scripts\\python tools\\map_overlays.py
"""
import hashlib
import json
from pathlib import Path

EXE = Path("game/FALCONCD.EXE").read_bytes()
IDA = Path("analysis/ida_falconcd")

scope = json.loads((IDA / "overlay_scope.json").read_text())["scope"]
place = json.loads((IDA / "overlay_placement.json").read_text())
cls = json.loads((IDA / "classification.json").read_text())
lst = json.loads((IDA / "dst_list.json").read_text())
entries = json.loads((IDA / "overlay_entries.json").read_text())


def rec_for(ea):
    for p in place:
        if p.get("ida_ea") is not None and p["ida_len"] and \
           p["ida_ea"] <= ea < p["ida_ea"] + p["ida_len"]:
            return p
    return None


def blob_for(lo, hi):
    rec = rec_for(lo)
    if rec is None:
        return None
    off = lo - rec["ida_ea"]
    return EXE[rec["data_file"] + off: rec["data_file"] + off + (hi - lo)]


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
holes = []
for blk in scope:
    lo, hi = blk["lo"], blk["hi"]
    blob = blob_for(lo, hi)
    if blob is None or len(blob) != hi - lo:
        # can't read bytes -- emit an empty block, no holes
        blocks.append({"lo": lo, "hi": hi, "size": hi - lo,
                       "printable_frac": 0, "head_hex": "", "head_ascii": "",
                       "head_data": False, "strings": [], "n_strings": 0,
                       "dsts": 0, "refs": 0, "strong": 0, "rtlink_entries": [],
                       "functions": [], "covered_bytes": 0, "dst_eas": [],
                       "no_bytes": True})
        continue
    runs = runs_of(blob, lo)
    printable = sum(1 for x in blob if 0x20 <= x < 0x7F or x == 0)
    head = blob[:16]
    hd = sum(1 for x in head if 0x20 <= x < 0x7F or x == 0)
    bdst = [r for r in lst if lo <= r["ea"] < hi]
    bent = [e["entry_ea"] for e in entries
            if e.get("entry_ea") and lo <= e["entry_ea"] < hi]
    bfn = [(v["ea"], v["ea"] + v["size"], k) for k, v in cls.items()
           if v.get("ea") is not None and lo <= v["ea"] < hi]
    covered = sum(e - s for s, e, _ in bfn)
    blocks.append({
        "lo": lo, "hi": hi, "size": hi - lo,
        "printable_frac": round(printable / max(1, len(blob)), 3),
        "head_hex": head.hex(),
        "head_ascii": "".join(chr(x) if 0x20 <= x < 0x7F else "." for x in head),
        "head_data": hd >= 8,
        "strings": [{"ea": ea, "len": n, "text": t} for ea, n, t in runs[:16]],
        "n_strings": len(runs),
        "dsts": len(bdst), "refs": sum(r["n"] for r in bdst),
        "strong": 0, "rtlink_entries": bent,
        "functions": [{"key": k, "ea": s, "size": e - s} for s, e, k in bfn],
        "covered_bytes": covered,
        "dst_eas": [r["ea"] for r in bdst],
    })
    # candidate holes: merged string clusters (>=6, adjacent) + data-led heads
    # merge adjacent runs (gap <= 8) into clusters
    merged = []
    for ea, n, t in runs:
        if merged and ea - (merged[-1][0] + merged[-1][1]) <= 8:
            pe, pn, pt = merged[-1]
            merged[-1] = (pe, ea + n - pe, pt + t)
        else:
            merged.append((ea, n, t))
    for ea, n, t in merged:
        if n >= 6:
            raw = blob[ea - lo: ea - lo + n]
            if len(raw) == n:
                holes.append({
                    "lo": ea, "hi": ea + n, "size": n,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "why": "string:" + t[:40], "block": blk["name"],
                })
    # data-led head: if the block starts with data-like bytes and no fn covers
    # the first 16, pin a small head hole only if no fn overlaps it
    if hd >= 8 and not any(s <= lo < e for s, e, _ in bfn) and 16 <= hi - lo:
        raw = blob[:16]
        holes.append({
            "lo": lo, "hi": lo + 16, "size": 16,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "why": "data-head", "block": blk["name"],
        })

n_fn = sum(len(b["functions"]) for b in blocks)
n_dst = sum(b["dsts"] for b in blocks)
n_ref = sum(b["refs"] for b in blocks)
total_bytes = sum(b["size"] for b in blocks)
covered = sum(b["covered_bytes"] for b in blocks)

# dedupe holes by lo (keep first)
seen = set()
uh = []
for h in holes:
    if h["lo"] not in seen:
        seen.add(h["lo"])
        uh.append(h)
holes = uh

out = {
    "range": [scope[0]["lo"], scope[-1]["hi"]],
    "blocks": blocks,
    "holes": holes,
    "functions": [{"key": k, "ea": v["ea"], "size": v["size"]}
                  for b in blocks for k, v in
                  [(f["key"], f) for f in b["functions"]]],
    "dst_total": n_dst,
    "ref_total": n_ref,
}
(IDA / "overlay_map.json").write_text(json.dumps(out, indent=1))
print("overlay_map: %d blocks, %d bytes, covered %d (%.0f%%)" % (
    len(blocks), total_bytes, covered, 100.0 * covered / max(1, total_bytes)))
print("  functions: %d   dsts: %d   refs: %d" % (n_fn, n_dst, n_ref))
print("  holes: %d candidates / %d B" % (len(holes), sum(h["size"] for h in holes)))
print("wrote analysis/ida_falconcd/overlay_map.json")