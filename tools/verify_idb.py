"""Semantic IDB integrity check (read-only) -- run with run_idat.bat.

MD5 is NOT a usable integrity signal for the .i64: idat rewrites the file on
every invocation (timestamps / autoanalysis), so a hash comparison against a
backup false-alarms after the very next run, and matching a freshly-made copy
proves nothing. The invariant that actually matters is semantic: every
function still exists at its recorded EA with its recorded span and name
(finding 50).

Exit code is informational only -- callers should print the VERDICT line.

Output: analysis/ida_falconcd/integrity.log
"""
import json

import ida_funcs
import idaapi
import idc

FB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\function_bytes.json"
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

ok = not (missing or span or renamed)
log.append("ida function count      : %d  (ground truth: %d)"
           % (ida_funcs.get_func_qty(), len(fb)))
log.append("missing functions       : %d  %s" % (len(missing), missing[:8]))
log.append("span mismatch (ea/size) : %d  %s" % (len(span), span[:8]))
log.append("name mismatch           : %d  %s" % (len(renamed), renamed[:5]))
log.append("VERDICT: %s" % ("INTACT" if ok else "DAMAGED"))
open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)