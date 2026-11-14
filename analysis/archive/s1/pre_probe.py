"""Read-only (DBFL_KILL): DS ranges, func flags, names/comments inside to-be-cleared ranges. Output analysis/s1/pre.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_segregs, ida_segment, ida_name
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\pre.txt"
DS = idaapi.str2reg("ds")
L = []
def para(v):
    return None if v in (idaapi.BADSEL, 0xFFFF, 0xFFFFFFFF) else ida_segment.sel2para(v)
try:
    for new, old, end in ((0x106EE2, 0x106EEC, 0x106F3A), (0x108430, 0x10843D, 0x1084A6), (0x10CE30, 0x10CFA6, 0x10CFEC)):
        L.append("=== new %X old %X end %X" % (new, old, end))
        f = ida_funcs.get_func(old)
        L.append("  old func %X-%X flags %X name %r user=%s" % (f.start_ea, f.end_ea, f.flags, idaapi.get_name(old), ida_bytes.has_user_name(ida_bytes.get_flags(old))))
        for a in (new, old, new + 1, end - 1):
            L.append("  DS@%X = %s" % (a, para(ida_segregs.get_sreg(a, DS))))
        rr = ida_segregs.sreg_range_t()
        ida_segregs.get_sreg_range(rr, new, DS)
        L.append("  DS range at new: %X..%X tag %d val %s" % (rr.start_ea, rr.end_ea, rr.tag, para(rr.val)))
        ida_segregs.get_sreg_range(rr, old, DS)
        L.append("  DS range at old: %X..%X tag %d val %s" % (rr.start_ea, rr.end_ea, rr.tag, para(rr.val)))
        for a in range(new, end):
            fl = ida_bytes.get_flags(a)
            nm = idaapi.get_name(a)
            cm = idc.get_cmt(a, 0), idc.get_cmt(a, 1)
            if (ida_bytes.has_user_name(fl) and a != old) or any(cm) or ida_bytes.get_flags(a) & 0x2000000:
                L.append("  item %X name=%r cmt=%s flags=%X" % (a, nm, cm, fl))
        L.append("  frame/tails: frame=%X tails=%d" % (f.frame, f.tailqty))
    for a in (0x10931E, 0x109445, 0x129F7, 0x12B12):
        L.append("%X name=%r DS=%s" % (a, idaapi.get_name(a), para(ida_segregs.get_sreg(a, DS))))
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
