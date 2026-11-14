"""Read-only (DBFL_KILL): item dump of 10B4E8..10B6E0 with owner, kind, xrefs.  Output: analysis/s1/menu_dis.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\menu_dis.txt"
L = []
try:
    a = ida_bytes.get_item_head(0x10B4E8)
    while a < 0x10B6E0:
        g = ida_funcs.get_func(a)
        fl = ida_bytes.get_flags(a)
        k = "C" if ida_bytes.is_code(fl) else "D"
        xs = ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0) if x.type != 21]
        L.append("%X [%s]%s %s %s" % (a, ("%X" % g.start_ea) if g else "-", k, idc.generate_disasm_line(a, 0),
                                      ("<- " + ",".join(xs[:4])) if xs else ""))
        a += ida_bytes.get_item_size(a)
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
