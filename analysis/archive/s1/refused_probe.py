"""Read-only (DBFL_KILL): the refused call targets, with the neighbouring existing function.  Output: analysis/s1/refused.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\refused.txt"
# (label, lo, hi)
W = [("106EE2", 0x106ED0, 0x106F20), ("108430", 0x108420, 0x108470), ("109445", 0x109430, 0x109470),
     ("10CE30", 0x10CE20, 0x10CE50), ("1129F7?", 0x129F7 - 0x10, 0x129F7 + 0x30), ("10931E", 0x109318, 0x109350)]
L = []


def line(a):
    g = ida_funcs.get_func(a)
    xs = ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0) if x.type != 21]
    b = ida_bytes.get_bytes(a, max(ida_bytes.get_item_size(a), 1)) or b""
    return "%X [%s] %-18s %s %s" % (a, ("%X" % g.start_ea) if g else "-", b.hex(), idc.generate_disasm_line(a, 0),
                                    ("<- " + ",".join(xs[:5])) if xs else "")


try:
    for lab, lo, hi in W:
        L.append("=== " + lab)
        a = lo
        while a < hi:
            L.append(line(a))
            a += max(ida_bytes.get_item_size(a), 1)
        L.append("")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
