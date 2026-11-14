"""Read-only (DBFL_KILL): disassembly (owner function, item kind) of selected address ranges.
Output: analysis/s1/orphan_dis.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan_dis.txt"
RUNS = [(0x12BF60, 0x12C010), (0x12C960, 0x12CB40), (0x12CCD0, 0x12CD10)]
L = []
try:
    for lo, hi in RUNS:
        L.append("=== %X..%X" % (lo, hi))
        a = ida_bytes.get_item_head(lo)
        while a < hi:
            g = ida_funcs.get_func(a)
            fl = ida_bytes.get_flags(a)
            k = "C" if ida_bytes.is_code(fl) else ("A" if ida_bytes.is_align(fl) else "D")
            L.append("%X [%s]%s %s" % (a, ("%X" % g.start_ea) if g else "-", k, idc.generate_disasm_line(a, 0)))
            a += ida_bytes.get_item_size(a)
        L.append("")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
