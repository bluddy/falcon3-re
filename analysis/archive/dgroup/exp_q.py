"""Experiment (copy only): is the auto queue empty on load; does auto_wait alone create functions?"""
import idaapi, ida_auto, ida_funcs, ida_loader, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\dgroup\exp_q.txt"
out = ["auto_is_ok on load %s funcs %d" % (ida_auto.auto_is_ok(), ida_funcs.get_func_qty())]
before = set(idautils.Functions())
ida_auto.auto_wait()
after = set(idautils.Functions())
out.append("after auto_wait funcs %d new %s" % (len(after), sorted(hex(x) for x in after - before)[:30]))
open(OUT, "w").write("\n".join(out))
ida_loader.set_database_flag(ida_loader.DBFL_KILL)
idaapi.qexit(0)
