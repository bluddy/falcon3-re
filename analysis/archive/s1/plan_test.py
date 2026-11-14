"""Test: does apply_orphan_funcs PLAN mode crash? Add debug output."""
import os, traceback, idaapi, ida_loader
from pathlib import Path

LOG = Path("C:/Users/ybarnoy/projects/falcon3/analysis/s1/plan_test_out.log")
log = []

try:
    log.append("OFMODE: %r" % os.environ.get("OFMODE"))
    
    # Try to import the script's key items to narrow down the crash
    import sys
    sys.path.insert(0, "C:/Users/ybarnoy/projects/falcon3/tools")
    
    # Check if idautils etc. are OK
    import idautils, idc, ida_funcs, ida_bytes
    log.append("imports OK")
    
    # Try running just the PLAN check
    PLAN = os.environ.get("OFMODE") == "plan"
    log.append("PLAN = %s" % PLAN)
    
    if PLAN:
        log.append("Would run PLAN mode")
        # Try to count functions
        n = sum(1 for _ in idautils.Functions())
        log.append("function count: %d" % n)
        
except Exception:
    log.append("ERROR:\n" + traceback.format_exc())

LOG.write_text("\n".join(log))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
