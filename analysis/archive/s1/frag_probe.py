import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\frag.txt"
L = []
def fn(a):
    f = ida_funcs.get_func(a)
    return ("%X-%X %s" % (f.start_ea, f.end_ea, idaapi.get_name(f.start_ea))) if f else "-"
try:
    for a in (0x6EC17, 0x6EF1F, 0x2E1E8, 0x22C8B, 0x67F77, 0x69720, 0x167449):
        f = ida_funcs.get_func(a)
        L.append("=== %X func %s  xrefs to: %s" % (a, fn(a), ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0)]))
        lo = idc.prev_head(a, a - 40)
        lo = idc.prev_head(lo, a - 40)
        lo = idc.prev_head(lo, a - 40)
        x = lo
        n = 0
        while n < 14 and x < a + 48:
            h = ida_bytes.get_item_head(x)
            sz = max(ida_bytes.get_item_size(h), 1)
            L.append("  %X %-12s %-34s f=%s%s" % (h, (ida_bytes.get_bytes(h, sz) or b"").hex()[:24], idc.generate_disasm_line(h, 0)[:34], fn(h).split()[0],
                                              "" if ida_bytes.is_code(ida_bytes.get_flags(h)) else " [DATA]"))
            x = h + sz
            n += 1
        L.append("")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
