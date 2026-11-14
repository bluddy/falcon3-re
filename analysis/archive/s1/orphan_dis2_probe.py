"""Read-only (DBFL_KILL): disassembly (owner function, item kind) of selected ranges.
Output: analysis/s1/orphan_dis2.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan_dis2.txt"
RUNS = [(0x10B370, 0x10B4F8), (0x10B6A0, 0x10B730), (0x10B880, 0x10B8A0), (0x10BA30, 0x10BA60),
        (0x129F7, 0x12A10), (0x6DFF0, 0x6E000), (0x6E16E, 0x6E190), (0x106EE2, 0x106F10),
        (0x108430, 0x108460), (0x10931E, 0x109350), (0x109445, 0x109470), (0x10CE30, 0x10CE60)]
L = []
try:
    for lo, hi in RUNS:
        L.append("=== %X..%X" % (lo, hi))
        a = ida_bytes.get_item_head(lo)
        while a < hi:
            g = ida_funcs.get_func(a)
            fl = ida_bytes.get_flags(a)
            k = "C" if ida_bytes.is_code(fl) else ("A" if ida_bytes.is_align(fl) else "D")
            xs = ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0) if x.type != 21]
            L.append("%X [%s]%s %s %s" % (a, ("%X" % g.start_ea) if g else "-", k, idc.generate_disasm_line(a, 0),
                                          ("<- " + ",".join(xs[:4])) if xs else ""))
            a += ida_bytes.get_item_size(a)
        L.append("")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
