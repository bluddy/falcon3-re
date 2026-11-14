"""
autoq_probe.py  —  drain the auto queue on a PROBE copy and record new functions.
Run: idat -A -S"analysis/s1/autoq_probe.py" analysis/s1/probe_autoq.i64
"""
import idc, ida_funcs, idautils, idaapi
import json
from pathlib import Path

LOG  = Path("analysis/s1/autoq_probe.log")
OUT  = Path("analysis/s1/autoq_probe.json")

before = set(idautils.Functions())
log = ["before: %d functions" % len(before)]

# Drain the auto queue
idc.auto_wait()

after = set(idautils.Functions())
new_fns = sorted(after - before)
log.append("after: %d functions (+%d)" % (len(after), len(new_fns)))

results = []
for ea in new_fns:
    f = ida_funcs.get_func(ea)
    if f and f.start_ea == ea:
        import idc as _idc
        last_m = _idc.print_insn_mnem(idc.prev_head(f.end_ea, f.start_ea))
        results.append({
            "ea": ea, "end": f.end_ea, "size": f.end_ea - f.start_ea,
            "seg": idaapi.get_segm_name(idaapi.getseg(ea)),
            "last": last_m,
            "name": idc.get_func_name(ea)
        })
        log.append("  0x%X..0x%X (%dB) seg=%s last=%r name=%s" % (
            ea, f.end_ea, f.end_ea-ea, results[-1]["seg"], last_m, results[-1]["name"]))

OUT.write_text(json.dumps(results, indent=1))
LOG.write_text("\n".join(log))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
