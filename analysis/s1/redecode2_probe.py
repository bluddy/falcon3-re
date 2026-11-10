"""Read-only (DBFL_KILL on a COPY): why create_insn fails at 106EEA / 10843C / 10CFA5.  Output: analysis/s1/redecode2.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_ua, ida_fixup, ida_segment
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\redecode2.txt"
L = []
try:
    for a in (0x106EEA, 0x10843C, 0x10CFA5):
        seg = ida_segment.getseg(a)
        L.append("=== %X seg=%s bitness=%d" % (a, ida_segment.get_segm_name(seg), seg.bitness))
        for b in range(a - 2, a + 6):
            fd = ida_fixup.fixup_data_t()
            has = ida_fixup.get_fixup(fd, b)
            L.append("  fixup at %X: %s" % (b, ("type=%d off=%X" % (fd.get_type(), fd.off)) if has else "-"))
        ins = ida_ua.insn_t()
        n = ida_ua.decode_insn(ins, a)
        L.append("  decode_insn -> %d  (%s)" % (n, ida_bytes.get_bytes(a, 4).hex()))
        fl = ida_bytes.get_flags(a)
        L.append("  flags=%X is_code=%s is_data=%s head=%X size=%d" % (fl, ida_bytes.is_code(fl), ida_bytes.is_data(fl),
                                                                      ida_bytes.get_item_head(a), ida_bytes.get_item_size(a)))
        ida_bytes.del_items(a, ida_bytes.DELIT_SIMPLE, 3)
        L.append("  after del 3B: create_insn -> %d" % ida_ua.create_insn(a))
        ida_bytes.del_items(a, ida_bytes.DELIT_EXPAND, 3)
        L.append("  after del(EXPAND) create_insn -> %d  %s" % (ida_ua.create_insn(a), idc.generate_disasm_line(a, 0)))
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
