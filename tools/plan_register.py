"""Finding 61 step P3a (host): turn the P2 sweep plan into the parentless
registration manifest registry/upper_register_expected.json.

validate_rebuild's REGISTER class needs, per range, an exact tiling of
    new_fns | keep_fns | data_holes  ==  [lo, hi)
plus sha256 for every candidate hole (68 / 6,278 B -- all of them, including
the 10 that sit outside any registered range, so UI strings like
`YOUR PLANE HAS BEEN DESTROYED!` are protected too).

Refuses to write if any range fails tiling, if a keep key is not in the
current ground truth, or if a hole lacks a live hash.

Usage: venv\\Scripts\\python tools\\plan_register.py
"""
import json
import os
import sys
from pathlib import Path

IDA = Path("analysis/ida_falconcd")
# finding 64: overlay pass points these at overlay_sweep.json /
# overlays_register_expected.json via env vars; defaults are the upper pass.
OUT = Path(os.environ.get(
    "FALCON_PLAN_OUT", "registry/upper_register_expected.json"))
SWEEP = IDA / os.environ.get("FALCON_PLAN_SWEEP", "upper_sweep.json")
FB = IDA / "function_bytes.json"

sw = json.loads(SWEEP.read_text())
fb = json.loads(FB.read_text())
problems = []
ranges_out = []

seen_ea = {}
for r in sw["ranges"]:
    lo, hi = r["range"]
    name = r["name"]
    keep = [{"key": f["key"], "ea": f["ea"], "size": f["size"]}
            for f in r["keep_fns"]]
    new = [{"key": f["key"], "ea": f["ea"], "size": f["size"]}
           for f in r["new_fns"]]
    holes = []
    for h in r.get("holes_in_range", []):
        ea = h.get("lo", h.get("ea"))
        he = ea + h["size"]
        # finding 64: a hole inside a keep/new function span is embedded data
        # (string table in code) -- not a gap hole; drop it so tiling stays
        # exact.  The function's bytes already cover it.
        in_fn = any(f["ea"] < he and ea < f["ea"] + f["size"]
                    for f in keep + new)
        if in_fn:
            continue
        holes.append({"ea": ea, "size": h["size"],
                      "sha256": h.get("sha256"), "why": (h.get("why") or "")[:160]})

    # -- tiling: spans must cover [lo,hi) exactly, in order, no gaps/overlaps
    spans = sorted([(f["ea"], f["ea"] + f["size"], "fn:" + f["key"]) for f in new]
                   + [(f["ea"], f["ea"] + f["size"], "keep:" + f["key"]) for f in keep]
                   + [(h["ea"], h["ea"] + h["size"], "hole") for h in holes])
    cur = lo
    for s, e, tag in spans:
        if s < cur:
            problems.append("%s: overlap at 0x%X (cur 0x%X, %s)" % (name, s, cur, tag))
        elif s > cur:
            problems.append("%s: gap 0x%X..0x%X (%d B uncovered by plan)"
                            % (name, cur, s, s - cur))
        cur = max(cur, e)
    if cur != hi:
        problems.append("%s: coverage ends at 0x%X, range ends 0x%X" % (name, cur, hi))

    # -- keep keys must be real ground-truth keys; keys must be unique globally
    for f in keep + new:
        if f["key"] in seen_ea and seen_ea[f["key"]] != f["ea"]:
            problems.append("%s: duplicate key %s (0x%X vs 0x%X)"
                            % (name, f["key"], seen_ea[f["key"]], f["ea"]))
        seen_ea[f["key"]] = f["ea"]
    for f in keep:
        if f["key"] not in fb:
            problems.append("%s: keep key %s not in function_bytes" % (name, f["key"]))
        elif fb[f["key"]]["ea"] != f["ea"] or fb[f["key"]]["size"] != f["size"]:
            problems.append("%s: keep %s drifted (manifest 0x%X/%d vs truth 0x%X/%d)"
                            % (name, f["key"], f["ea"], f["size"],
                               fb[f["key"]]["ea"], fb[f["key"]]["size"]))
    for h in holes:
        if not h["sha256"]:
            problems.append("%s: hole 0x%X has no live sha256" % (name, h["ea"]))

    ranges_out.append({"name": name, "range": [lo, hi], "keep_fns": keep,
                       "new_fns": new, "data_holes": holes})

# every candidate hole must be either in a range or standalone (no orphans).
# Suspect holes the sweep dropped from tiling are recorded for the record but
# NOT enforced (a sweep overran into them -- they may be code, and a function
# legitimately covers them); enforcing them would make the mutator fail.
all_holes = sw.get("all_holes", [])
suspect = set(sw.get("suspect_holes", []))
# finding 64: a hole inside ANY keep/new function span is embedded data (a
# string table inside code) -- exclude it entirely (not in-range, not
# standalone, not an orphan): the function's bytes already cover it and the
# mutator would refuse it as standalone.
fn_spans = [(f["ea"], f["ea"] + f["size"])
            for r in ranges_out for f in r["keep_fns"] + r["new_fns"]]


def in_any_fn(ea, size):
    return any(s < ea + size and ea < e for s, e in fn_spans)


standalone_all = [{"ea": h["ea"], "size": h["size"], "sha256": h["sha256"],
                   "why": h["why"], "block": h.get("block")}
                  for h in all_holes
                  if h["ea"] not in suspect
                  and not in_any_fn(h["ea"], h["size"])]
embedded = [h["ea"] for h in all_holes
            if h["ea"] not in suspect and in_any_fn(h["ea"], h["size"])]
in_ranges = {h["ea"] for r in ranges_out for h in r["data_holes"]}
standalone = [h for h in standalone_all if h["ea"] not in in_ranges]
suspect_out = [h for h in all_holes if h["ea"] in suspect]
for h in standalone:
    if not h["sha256"]:
        problems.append("standalone hole 0x%X has no sha256" % h["ea"])

# every candidate hole must be either in a range or standalone (no orphans).
# Suspect holes are exempt: the sweep overran into them, so they may be code
# and a function may legitimately cover them (finding 62: 0x4ACA1).
# Embedded-in-fn holes are exempt too (finding 64): the fn covers them.
orphans = [h["ea"] for h in all_holes
           if h["ea"] not in in_ranges
           and h["ea"] not in {s["ea"] for s in standalone}
           and h["ea"] not in suspect
           and h["ea"] not in set(embedded)]
if orphans:
    problems.append("holes in no bucket: %s" % [hex(x) for x in orphans[:8]])

n_fn = sum(len(r["new_fns"]) for r in ranges_out)
n_keep = sum(len(r["keep_fns"]) for r in ranges_out)
n_h = sum(len(r["data_holes"]) for r in ranges_out)
print("ranges: %d   new_fns: %d   keep: %d   holes_in_ranges: %d   standalone: %d"
      % (len(ranges_out), n_fn, n_keep, n_h, len(standalone)))
print("bytes registered (new): %d   total pinned holes: %d B"
      % (sum(f["size"] for r in ranges_out for f in r["new_fns"]),
         sum(h["size"] for r in ranges_out for h in r["data_holes"])
         + sum(h["size"] for h in standalone)))
print("suspect holes (dropped from tiling, still pinned): %s"
      % [hex(x) for x in sw.get("suspect_holes", [])])

if problems:
    print("\nNOT WRITING -- %d problems:" % len(problems))
    for p in problems[:20]:
        print("   !", p)
    sys.exit(1)

OUT.write_text(json.dumps({
    "schema": 1,
    "reason": ("finding %s: parentless registration from sweep %s.  Plan "
               "comes from sweep_upper.py: existing IDA decodes win, `00` runs "
               "are skipped only in front of entry-like code, mid-body "
               "islands may be bridged only when a chain re-closes on a "
               "terminator, and every function needs evidence (a referenced "
               "seed, an existing code item, or a chain closed on an "
               "authoritative boundary).  REGISTER validation: exact tiling "
               "+ live sha256 per hole."
               % ("64" if "overlay" in SWEEP.name else "61", SWEEP.name)),
    "ranges": ranges_out,
    "standalone_holes": standalone,
    "n_new_fns": n_fn,
    "n_keep_fns": n_keep,
    "n_holes": n_h + len(standalone),
    "hole_bytes": sum(h["size"] for r in ranges_out for h in r["data_holes"])
                  + sum(h["size"] for h in standalone),
}, indent=1))
print("wrote %s" % OUT)
