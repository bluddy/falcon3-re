#!/usr/bin/env python3
"""Finding 64: filter body-integrity-broken new_fns out of the overlay
manifest and convert their spans to sha256-pinned data_holes so tiling stays
exact.  The 5 broken fns have an undecodable byte mid-span (not clean
functions) -- their bytes become pinned holes instead.

Reads the 5 addresses from analysis/ida_falconcd/diag_ovl_integrity.log,
reads bytes from FALCONCD.EXE via overlay_placement for sha256.

Usage: venv\\Scripts\\python tools\\filter_overlay_manifest.py
"""
import hashlib
import json
import re
from pathlib import Path

EXE = Path("game/FALCONCD.EXE").read_bytes()
IDA = Path("analysis/ida_falconcd")
MAN = Path("registry/overlays_register_expected.json")
LOG = IDA / "diag_ovl_integrity.log"
PLACE = IDA / "overlay_placement.json"

place = json.loads(PLACE.read_text())
# parse bad fns from the integrity log
bad = {}   # key -> (ea, size)
for line in LOG.read_text().splitlines():
    m = re.match(r"\s+(\S+)\s+0x([0-9A-Fa-f]+)\.\.0x([0-9A-Fa-f]+)\s+size=(\d+)", line)
    if m:
        key = m.group(1)
        ea = int(m.group(2), 16)
        size = int(m.group(4))
        bad[key] = (ea, size)
print("bad fns to filter: %d" % len(bad))

def rec_for(ea):
    for p in place:
        if p.get("ida_ea") is not None and p["ida_len"] and \
           p["ida_ea"] <= ea < p["ida_ea"] + p["ida_len"]:
            return p
    return None

def sha_span(ea, size):
    rec = rec_for(ea)
    if rec is None:
        return None
    off = ea - rec["ida_ea"]
    raw = EXE[rec["data_file"] + off: rec["data_file"] + off + size]
    return hashlib.sha256(raw).hexdigest() if len(raw) == size else None

man = json.loads(MAN.read_text())
ranges = man["ranges"]
new_ranges = []
converted = []
for r in ranges:
    keep = r["keep_fns"]
    holes = list(r["data_holes"])
    new = []
    for f in r["new_fns"]:
        if f["key"] in bad:
            # convert span to a data hole
            ea, size = bad[f["key"]]
            sha = sha_span(ea, size)
            holes.append({"ea": ea, "size": size, "sha256": sha,
                          "why": "body-integrity-broken:" + f["key"]})
            converted.append((f["key"], ea, size, sha is not None))
        else:
            new.append(f)
    # drop the range entirely if no fns and no keep (only holes)
    if not new and not keep:
        # keep the range if it has holes (still needs tiling) -- but a range
        # with only holes tiles fine.  Keep it.
        pass
    r2 = dict(r)
    r2["new_fns"] = new
    r2["data_holes"] = holes
    new_ranges.append(r2)

n_fn = sum(len(r["new_fns"]) for r in new_ranges)
n_h = sum(len(r["data_holes"]) for r in new_ranges)
n_keep = sum(len(r["keep_fns"]) for r in new_ranges)
hole_bytes = sum(h["size"] for r in new_ranges for h in r["data_holes"])
man["ranges"] = new_ranges
man["n_new_fns"] = n_fn
man["n_keep_fns"] = n_keep
man["n_holes"] = n_h
man["hole_bytes"] = hole_bytes
man["reason"] = man.get("reason", "") + (
    "  5 body-integrity-broken new_fns converted to data_holes (undecodable "
    "byte mid-span): " + ", ".join(c[0] for c in converted) + ".")
MAN.write_text(json.dumps(man, indent=1))
print("filtered: new_fns %d -> %d, holes -> %d (%d B)" % (
    n_fn + len(bad), n_fn, n_h, hole_bytes))
for k, ea, size, ok in converted:
    print("  %s -> hole 0x%X..0x%X sha=%s" % (k, ea, ea + size, "ok" if ok else "MISSING"))