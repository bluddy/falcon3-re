"""Read-only (DBFL_KILL): disassembly/bytes around the 5 call sites whose return address is not code.
Output: analysis/s1/site5.txt"""
import traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\site5.txt"
L = []
try:
    for lo, hi in [(0x2F990, 0x2F9D0), (0x326F0, 0x32720), (0x32730, 0x32760), (0x32A30, 0x32A60), (0x32A90, 0x32AC0)]:
        L.append("=== %X..%X" % (lo, hi))
        ea = ida_bytes.get_item_head(lo)
        while ea < hi:
            g = ida_funcs.get_func(ea)
            L.append("%X [%s] %-30s %s" % (ea, ("%X" % g.start_ea) if g else "-",
                                           ida_bytes.get_bytes(ea, min(ida_bytes.get_item_size(ea), 8)).hex(),
                                           idc.generate_disasm_line(ea, 0)))
            ea += ida_bytes.get_item_size(ea)
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
