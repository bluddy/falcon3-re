import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_ua, ida_auto, ida_segregs, ida_segment, ida_ida
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\frag6.txt"
L = []
def sr(a):
    out = []
    for r in ("ds", "es", "cs", "ss"):
        out.append("%s=%X" % (r, ida_segregs.get_sreg(a, idaapi.str2reg(r)) & 0xFFFFFFFF))
    return " ".join(out)
try:
    for a, n in ((0x69722, 8), (0x6EF30, 8), (0x16743E, 18), (0x69720, 6)):
        L.append("=== %X  bytes %s  sregs %s" % (a, ida_bytes.get_bytes(a, 8).hex(), sr(a)))
        ida_bytes.del_items(a - 4, ida_bytes.DELIT_SIMPLE, n + 8)
        L.append("  flags after del: %X unknown=%s" % (ida_bytes.get_flags(a), ida_bytes.is_unknown(ida_bytes.get_flags(a))))
        ins = ida_ua.insn_t()
        L.append("  decode_insn=%d" % ida_ua.decode_insn(ins, a))
        L.append("  create_insn=%d  -> %s" % (ida_ua.create_insn(a), idc.generate_disasm_line(a, 0)))
        L.append("  idc.create_insn=%s" % idc.create_insn(a))
        L.append("  auto_make_code: %s" % ida_auto.auto_make_code(a))
        L.append("  flags now %X" % ida_bytes.get_flags(a))
        # does a data xref / name sit at the first byte?
        L.append("  name %r  has_name %s" % (idaapi.get_name(a), ida_bytes.has_any_name(ida_bytes.get_flags(a))))
        # try bytewise: create insns starting a few bytes before to resync
    ida_bytes.del_items(0x6EF30, ida_bytes.DELIT_SIMPLE, 0x40)
    r = [ida_ua.create_insn(0x6EF30)]
    L.append("clear 0x40 from 6EF30 then create_insn=%s" % r)
    L.append("seg bitness %d, inf 16bit? %s, proc %s" % (ida_segment.getseg(0x6EF30).bitness, ida_ida.inf_is_16bit(), ida_ida.inf_get_procname()))
    L.append("L %s" % idc.generate_disasm_line(0x6EF30, 0))
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
