import json
import traceback

import ida_segment
import ida_bytes
import ida_funcs
import idaapi
import ida_ua
import idautils

ROOT = r"C:\Users\yotam\projects\falcon3"
entries = json.load(open(ROOT + r"\analysis\ida_falconcd\overlay_entries.json"))
lines = []

reasons = {}
samples = {}
for e in entries:
    ea = e["entry_ea"]
    seg = ida_segment.getseg(ea)
    if seg is None:
        r = "no-segment"
    elif ida_funcs.get_func(ea) is not None:
        r = "already-func"
    else:
        ok_i = ida_ua.create_insn(ea)
        if not ok_i:
            r = "create_insn-failed"
        else:
            ok_f = ida_funcs.add_func(ea)
            if ok_f:
                r = "OK"
            else:
                r = "add_func-failed"
    reasons[r] = reasons.get(r, 0) + 1
    if r not in samples:
        samples[r] = (ea, e)

for r, n in sorted(reasons.items(), key=lambda x: -x[1]):
    ea, e = samples[r]
    seg = ida_segment.getseg(ea)
    lines.append("%-22s %4d  sample ea=0x%X row=%d seg=%s" % (
        r, n, ea, e["row"], seg.name if seg else "NONE"))

open(ROOT + r"\analysis\ida_falconcd\entry_diag.txt", "w").write("\n".join(lines))
idaapi.qexit(0)
