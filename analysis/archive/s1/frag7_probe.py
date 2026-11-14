import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils, ida_segregs
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\frag7.txt"
L = []
try:
    for a in (0x69723, 0x6EF31, 0x69705):
        f = ida_funcs.get_func(a)
        L.append("%X flags %X far=%s %X-%X name %s user=%s" % (a, f.flags, bool(f.flags & ida_funcs.FUNC_FAR), f.start_ea, f.end_ea, idaapi.get_name(a), ida_bytes.has_user_name(ida_bytes.get_flags(a))))
    for lo, hi in ((0x69700, 0x69730), (0x6EF1C, 0x6EF40)):
        rr = ida_segregs.sreg_range_t()
        a = lo
        while a < hi:
            if ida_segregs.get_sreg_range(rr, a, idaapi.str2reg("ds")):
                L.append("DS range %X-%X val %X tag %d" % (rr.start_ea, rr.end_ea, rr.val & 0xFFFFFFFF, rr.tag))
                a = max(rr.end_ea, a + 1)
            else:
                a += 1
    L.append("xrefs to 6EF30: %s" % [("%X" % x.frm, x.type, idc.generate_disasm_line(x.frm, 0)) for x in idautils.XrefsTo(0x6EF30, 0)])
    L.append("caller func: %s" % ida_funcs.get_func(0x6EEB6).start_ea)
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
