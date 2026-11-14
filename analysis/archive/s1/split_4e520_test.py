"""Test splitting 0x4E520 at 0x4E5B4."""
import os, traceback, idaapi, ida_funcs, ida_loader, idc
from pathlib import Path

LOG = Path("C:/Users/ybarnoy/projects/falcon3/analysis/s1/split_4e520_test.log")
log = []

try:
    f = ida_funcs.get_func(0x4E520)
    log.append("fn 0x4E520: start=0x%X end=0x%X" % (f.start_ea, f.end_ea) if f else "fn 0x4E520: not found")
    
    # Try the split
    r1 = ida_funcs.set_func_end(0x4E520, 0x4E5B4)
    log.append("set_func_end result: %s" % r1)
    
    r2 = ida_funcs.add_func(0x4E5B4, 0x4E803)
    log.append("add_func result: %s" % r2)
    
    f_new = ida_funcs.get_func(0x4E5B4)
    log.append("new fn at 0x4E5B4: %s" % (hex(f_new.end_ea) if f_new and f_new.start_ea == 0x4E5B4 else "not found"))

except Exception:
    log.append("ERROR:\n" + traceback.format_exc())

LOG.write_text("\n".join(log))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
