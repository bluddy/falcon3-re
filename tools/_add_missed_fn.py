"""Register the IDA-missed function sub_19D65 (0x19D65-0x19DA6) in the IDB."""
import traceback

import ida_funcs
import ida_loader
import ida_name
import idaapi

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\addfunc.log"

log = []
try:
    ea = 0x19D65
    ok = ida_funcs.add_func(ea, 0x19DA6)
    ida_name.set_name(ea, "sub_19D65", ida_name.SN_CHECK)
    log.append("add_func(0x19D65..0x19DA6) = %s" % ok)
    f = ida_funcs.get_func(ea)
    log.append("func now: %s" % (hex(f.start_ea) + "-" + hex(f.end_ea) if f else "NONE"))
    idaapi.auto_wait()
    ida_loader.save_database(IDB, 0)
    log.append("saved")
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
