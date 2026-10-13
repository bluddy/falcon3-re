"""Register IDA-missed functions from gap sweep (headless, batch).

Usage: cmd /c "tools\run_idat.bat tools\add_gap_functions.py"
"""
import json
import traceback

import ida_funcs
import ida_loader
import ida_name
import idaapi

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\addfunc_gap.log"
GAP_JSON = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\gap_candidates.json"

with open(GAP_JSON) as f:
    gaps = json.load(f)

code_gaps = [g for g in gaps if g['kind'] == 'gap-code']

log = []
try:
    for g in code_gaps:
        ea = g['start']
        end_ea = g['end']
        name = "sub_%X" % ea
        ok = ida_funcs.add_func(ea, end_ea)
        ida_name.set_name(ea, name, ida_name.SN_CHECK)
        f = ida_funcs.get_func(ea)
        log.append("%s add_func(0x%X..0x%X)=%s -> %s"
                   % (name, ea, end_ea, ok,
                      (hex(f.start_ea) + "-" + hex(f.end_ea)) if f else "NONE"))
    idaapi.auto_wait()
    ida_loader.save_database(IDB, 0)
    log.append("saved")
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)