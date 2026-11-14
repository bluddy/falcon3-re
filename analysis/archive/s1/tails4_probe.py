import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils, ida_name
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\tails4.txt"
L = []
try:
    for a in (0x4335A, 0x4334E, 0x43357, 0x42F6A):
        L.append("%X xrefs to: %s" % (a, ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0)]))
        L.append("   name=%r user=%s flags=%X" % (idaapi.get_name(a), ida_name.is_uname(idaapi.get_name(a) or ""), ida_bytes.get_flags(a)))
    f = ida_funcs.get_func(0x4335A)
    L.append("func %X-%X flags %X far=%s" % (f.start_ea, f.end_ea, f.flags, bool(f.flags & ida_funcs.FUNC_FAR)))
    L.append("4335A has user name flag: %s" % bool(ida_bytes.has_user_name(ida_bytes.get_flags(0x4335A))))
    f = ida_funcs.get_func(0x42F6A)
    L.append("func at 42F6A %X-%X %s" % (f.start_ea, f.end_ea, idaapi.get_name(f.start_ea)))
    a = 0x42F5B
    while a < f.end_ea:
        L.append("  %X %s" % (a, idc.generate_disasm_line(a, 0)))
        a = idc.next_head(a, f.end_ea + 1)
    L.append("before 4334E:")
    a = idc.prev_head(0x4334E, 0x43300)
    for _ in range(4):
        L.append("  %X %s  func=%s" % (a, idc.generate_disasm_line(a, 0), ("%X" % ida_funcs.get_func(a).start_ea) if ida_funcs.get_func(a) else None))
        a = idc.next_head(a, 0x43400)
    L.append("4334E raw: %s" % ida_bytes.get_bytes(0x43348, 20).hex())
    L.append("flags at 4334E: %X item head %X" % (ida_bytes.get_flags(0x4334E), ida_bytes.get_item_head(0x4334E)))
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
