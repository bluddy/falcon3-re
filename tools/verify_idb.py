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

import ida_bytes
import ida_funcs
import idaapi
import idc

FB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\function_bytes.json"
SPLITMAN = r"C:\Users\yotam\projects\falcon3\registry\subblock_split_expected.json"
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

# ---- data holes (finding 59) ----
hole_problems = []
holes_out = []
try:
    splits = json.loads(open(SPLITMAN).read()).get("splits", [])
except Exception:
    splits = []
for e in splits:
    # pre-carve iff the parent function still spans the whole old range
    # (planned children share the parent's start EA, so testing for a child's
    # presence alone would read the parent as carved)
    pf = ida_funcs.get_func(e["ea"])
    carved = not (pf and (pf.end_ea - pf.start_ea) == e["old_size"])
    for h in e["data_holes"]:
        ea, n = h["ea"], h["size"]
        raw = idc.get_bytes(ea, n)
        sha = (hashlib.sha256(raw).hexdigest()
               if raw is not None and len(raw) == n else None)
        in_fn = bool(ida_funcs.get_func(ea) or ida_funcs.get_func(ea + n - 1))
        is_data = bool(ida_bytes.is_data(ida_bytes.get_flags(ea)))
        holes_out.append({"ea": ea, "size": n, "sha256": sha,
                          "in_function": in_fn, "is_data": is_data,
                          "parent": e["key"], "carved": carved})
        if sha != h["sha256"]:
            hole_problems.append("hole 0x%X bytes: live %s != manifest %s"
                                 % (ea, sha, h["sha256"]))
        if carved:
            if in_fn:
                hole_problems.append("hole 0x%X is covered by a function" % ea)
            if not is_data:
                hole_problems.append("hole 0x%X is not flagged as data" % ea)
    log.append("carve %s: %d planned fns present=%s, %d data holes"
               % (e["key"], len(e["new_fns"]), carved, len(e["data_holes"])))
if splits:
    json.dump({"holes": holes_out}, open(HOLES_OUT, "w"))
    log.append("hole export: %s (%d holes)" % (HOLES_OUT, len(holes_out)))

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