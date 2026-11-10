"""Read-only (DBFL_KILL): disassembly of selected NORET-flagged functions + their callees' NORET status.
Output: analysis/s1/noret_dis.txt"""
import traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\noret_dis.txt"
TGT = [0x22DFF, 0x33116, 0x331E4, 0x3343E, 0x3F7A6, 0x4FE02, 0x3FD66, 0x3F861]
L = []
try:
    for t in TGT:
        f = ida_funcs.get_func(t)
        L.append("=== %X %s end=%X" % (t, idc.get_func_name(t), f.end_ea))
        ea = t
        n = 0
        while ea < f.end_ea and n < 140:
            L.append("%X  %s" % (ea, idc.generate_disasm_line(ea, 0)))
            nx = idc.next_head(ea, f.end_ea + 8)
            if nx == idaapi.BADADDR:
                break
            ea = nx
            n += 1
        L.append("-- end; next head %X: %s" % (f.end_ea, idc.generate_disasm_line(f.end_ea, 0)))
        L.append("-- callees:")
        seen = set()
        for h in idautils.FuncItems(t):
            for x in idautils.XrefsFrom(h, 0):
                if x.iscode and x.type in (16, 17, 18, 19):
                    g = ida_funcs.get_func(x.to)
                    if g and g.start_ea == x.to and x.to not in seen:
                        seen.add(x.to)
                        L.append("   %X %s noret=%s" % (x.to, idc.get_func_name(x.to), bool(g.flags & ida_funcs.FUNC_NORET)))
        L.append("")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
