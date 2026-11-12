import idc, ida_funcs, idaapi
from pathlib import Path
LOG = Path("C:/Users/ybarnoy/projects/falcon3/analysis/s1/state_check.log")
log = []

f1 = ida_funcs.get_func(0x683C5)
f2 = ida_funcs.get_func(0x6940B)
f3 = ida_funcs.get_func(0x6940E)

if f1: log.append("fn@683C5: start=0x%X end=0x%X name=%s" % (f1.start_ea, f1.end_ea, idc.get_func_name(f1.start_ea)))
else: log.append("fn@683C5: NONE")

if f2: log.append("fn@6940B: start=0x%X end=0x%X name=%s" % (f2.start_ea, f2.end_ea, idc.get_func_name(f2.start_ea)))
else: log.append("fn@6940B: NONE")

if f3: log.append("fn@6940E: start=0x%X end=0x%X" % (f3.start_ea, f3.end_ea))
else: log.append("fn@6940E: NONE")

idaapi.set_database_flag(idaapi.DBFL_KILL)
LOG.write_text("\n".join(log))
idc.qexit(0)
