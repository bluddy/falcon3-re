"""Read-only (DBFL_KILL): xrefs to 10CFA5/6/DF, items near 12B12, 12B11 retf; Output: analysis/s1/facts3.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\facts3.txt"
L = []
try:
    for a in (0x10CFA5, 0x10CFA6, 0x10CFDF, 0x10CFEC, 0x12B12, 0x12B62, 0x129F7, 0x109445, 0x10931E):
        L.append("%X xrefs: %s" % (a, ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0)]))
    f = ida_funcs.get_func(0x10CFA6)
    L.append("10CFA6 flags %X far=%s  name=%s" % (f.flags, bool(f.flags & ida_funcs.FUNC_FAR), idaapi.get_name(0x10CFA6)))
    for a in (0x10CE30, 0x129F7, 0x109445, 0x10931E):
        L.append("%X item head=%X flags=%X name=%r" % (a, ida_bytes.get_item_head(a), ida_bytes.get_flags(a), idaapi.get_name(a)))
    L.append("--- items 129FF..12A30 and 12B00..12B20")
    for lo, hi in ((0x129F7, 0x12A30), (0x12B00, 0x12B22)):
        a = lo
        while a < hi:
            L.append("%X sz=%d %s" % (a, ida_bytes.get_item_size(a), idc.generate_disasm_line(a, 0)))
            a += max(ida_bytes.get_item_size(a), 1)
    a = ida_bytes.get_item_head(0x12B11)
    L.append("head of 12B11 = %X size %d; item containing 12B12 head = %X" % (a, ida_bytes.get_item_size(a), ida_bytes.get_item_head(0x12B12)))
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
