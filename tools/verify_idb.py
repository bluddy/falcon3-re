"""Semantic IDB integrity check (read-only) -- run with run_idat.bat.

MD5 is NOT a usable integrity signal for the .i64: idat rewrites the file on
every invocation (timestamps / autoanalysis), so a hash comparison against a
backup false-alarms after the very next run, and matching a freshly-made copy
proves nothing. The invariant that actually matters is semantic: every
function still exists at its recorded EA with its recorded span and name
(finding 50).

Finding 59 adds the data-hole half of the carve gate: every hole planned in
registry/subblock_split_expected.json is hashed from the LIVE database and
exported to analysis/ida_falconcd/data_holes.json, where verify_rebuild reads
it.  Once the carve has happened (any planned child exists) a hole must also
be free of functions and flagged as data.

Exit code is informational only -- callers should print the VERDICT line.

Output: analysis/ida_falconcd/integrity.log
        analysis/ida_falconcd/data_holes.json
"""
import hashlib
import json
from collections import Counter

import ida_bytes
import ida_funcs
import idaapi
import idc

FB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\function_bytes.json"
SPLITMAN = r"C:\Users\yotam\projects\falcon3\registry\subblock_split_expected.json"
REGMAN = r"C:\Users\yotam\projects\falcon3\registry\upper_register_expected.json"
HOLES_OUT = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\data_holes.json"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\integrity.log"

fb = json.loads(open(FB).read())
log = []
missing, span, renamed = [], [], []

for k, v in fb.items():
    f = ida_funcs.get_func(v["ea"])
    if not f:
        missing.append(k)
        continue
    if f.start_ea != v["ea"]:
        span.append("%s start %s->%s" % (k, hex(v["ea"]), hex(f.start_ea)))
    elif (f.end_ea - f.start_ea) != v["size"]:
        span.append("%s size %d->%d" % (k, v["size"], f.end_ea - f.start_ea))
    want = v.get("name")
    if want and (idc.get_func_name(v["ea"]) or "") != want:
        renamed.append("%s want=%r got=%r" % (k, want, idc.get_func_name(v["ea"])))

# ---- data holes (finding 59) + parentless register holes (finding 61) ----
hole_problems = []
holes_out = []


def load_json(path):
    try:
        return json.loads(open(path).read())
    except Exception:
        return None


splits = (load_json(SPLITMAN) or {}).get("splits", [])
regdoc = load_json(REGMAN) or {}

specs = []
for e in splits:
    carved = not (ida_funcs.get_func(e["ea"]) and
                  (ida_funcs.get_func(e["ea"]).end_ea
                   - ida_funcs.get_func(e["ea"]).start_ea) == e["old_size"])
    for h in e["data_holes"]:
        specs.append(("split", h, e["key"], carved,
                      [e["ea"], e["ea"] + e["old_size"]]))
for rng in regdoc.get("ranges", []):
    lo, hi = rng["range"]
    carved = any(ida_funcs.get_func(f["ea"]) for f in rng["new_fns"])
    for h in rng["data_holes"]:
        if lo <= h["ea"] < hi:
            specs.append(("register", h, rng.get("name") or "%X..%X" % (lo, hi),
                          carved, [lo, hi]))
for h in regdoc.get("standalone_holes", []):
    specs.append(("standalone", h, "no range", False, None))

for kind, h, owner, carved, rng in specs:
    ea, n = h["ea"], h["size"]
    raw = idc.get_bytes(ea, n)
    sha = (hashlib.sha256(raw).hexdigest()
           if raw is not None and len(raw) == n else None)
    in_fn = bool(ida_funcs.get_func(ea) or ida_funcs.get_func(ea + n - 1))
    is_data = bool(ida_bytes.is_data(ida_bytes.get_flags(ea)))
    holes_out.append({"ea": ea, "size": n, "sha256": sha, "kind": kind,
                      "owner": owner, "range": rng, "carved": carved,
                      "in_function": in_fn, "is_data": is_data})
    if sha != h["sha256"]:
        hole_problems.append("[%s] hole 0x%X bytes: live %s != manifest %s"
                             % (kind, ea, sha, h["sha256"]))
    # register/standalone holes must NEVER be inside a function (they are
    # outside every registered range by construction, pre- and post-carve)
    if kind in ("register", "standalone"):
        if in_fn:
            hole_problems.append("[%s] hole 0x%X is covered by a function" % (kind, ea))
        if carved and kind == "register" and not is_data:
            hole_problems.append("[%s] hole 0x%X is not flagged as data" % (kind, ea))
    elif carved:
        if in_fn:
            hole_problems.append("[split] hole 0x%X is covered by a function" % ea)
        if not is_data:
            hole_problems.append("[split] hole 0x%X is not flagged as data" % ea)

if specs:
    json.dump({"holes": holes_out}, open(HOLES_OUT, "w"))
    log.append("hole export: %s (%d holes: %s)"
               % (HOLES_OUT, len(holes_out),
                  dict(Counter(s[0] for s in specs))))
    for rng in regdoc.get("ranges", []):
        carved = any(ida_funcs.get_func(f["ea"]) for f in rng["new_fns"])
        log.append("register %s: %d planned fns present=%s"
                   % (rng.get("name") or "%X..%X" % tuple(rng["range"]),
                      len(rng["new_fns"]), carved))

ok = not (missing or span or renamed or hole_problems)
log.append("ida function count      : %d  (ground truth: %d)"
           % (ida_funcs.get_func_qty(), len(fb)))
log.append("missing functions       : %d  %s" % (len(missing), missing[:8]))
log.append("span mismatch (ea/size) : %d  %s" % (len(span), span[:8]))
log.append("name mismatch           : %d  %s" % (len(renamed), renamed[:5]))
log.append("data-hole problems      : %d  %s" % (len(hole_problems), hole_problems[:5]))
log.append("VERDICT: %s" % ("INTACT" if ok else "DAMAGED"))
open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)