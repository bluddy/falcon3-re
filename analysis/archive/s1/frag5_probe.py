import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_ua, ida_fixup, ida_ida, ida_segment, ida_segregs, ida_idp
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\frag5.txt"
L = []
try:
    L.append("proc %s  bitness-of-seg: " % ida_ida.inf_get_procname())
    for a in (0x69720, 0x69722, 0x6EF30, 0x16743E, 0x6EC17, 0x2E1E8):
        seg = ida_segment.getseg(a)
        L.append("=== %X seg %s bitness %d  bytes %s" % (a, ida_segment.get_segm_name(seg), seg.bitness, ida_bytes.get_bytes(a, 6).hex()))
        for b in range(a - 1, a + 5):
            fd = ida_fixup.fixup_data_t()
            if ida_fixup.get_fixup(fd, b):
                L.append("   fixup at %X type %d off %X" % (b, fd.get_type(), fd.off))
        ins = ida_ua.insn_t()
        n = ida_ua.decode_insn(ins, a)
        L.append("   decode_insn -> %d" % n)
        fl = ida_bytes.get_flags(a)
        L.append("   flags %X code=%s head=%X size=%d" % (fl, ida_bytes.is_code(fl), ida_bytes.get_item_head(a), ida_bytes.get_item_size(a)))
        ida_bytes.del_items(a, ida_bytes.DELIT_SIMPLE, 8)
        r = ida_ua.create_insn(a)
        L.append("   after del 8B: create_insn -> %d  %s" % (r, idc.generate_disasm_line(a, 0)))
        L.append("   func at: %s" % (ida_funcs.get_func(a) and hex(ida_funcs.get_func(a).start_ea)))
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
