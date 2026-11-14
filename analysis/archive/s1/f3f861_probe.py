"""Read-only (DBFL_KILL): the end of 0x3F861 (does flow fall off the end, who owns 0x3FB22?) and the
rets inside it.  Output: analysis/s1/f3f861.txt"""
import traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f3f861.txt"
L = []
try:
    f = ida_funcs.get_func(0x3F861)
    L.append("end=%X noret=%s" % (f.end_ea, bool(f.flags & ida_funcs.FUNC_NORET)))
    for h in idautils.FuncItems(0x3F861):
        if idc.print_insn_mnem(h) in ("retn", "retf", "ret"):
            L.append("ret at %X" % h)
    L.append("--- tail")
    ea = 0x3FAF0
    while ea < 0x3FB60:
        g = ida_funcs.get_func(ea)
        L.append("%X [%s] %s" % (ea, ("%X" % g.start_ea) if g else "-", idc.generate_disasm_line(ea, 0)))
        ea = idc.next_head(ea, 0x3FB80)
        if ea == idaapi.BADADDR:
            break
    L.append("--- refs to 3FB22")
    for x in idautils.XrefsTo(0x3FB22, 0):
        L.append("  %X type=%d" % (x.frm, x.type))
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
