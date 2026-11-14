"""Experiment (copy only): what does set_default_sreg_value change?  Ranges of a
segment before/after changing its default DS (R29_3F70s, def 0) and SS (seg020)."""
import idaapi, ida_segregs, ida_segment, ida_loader, idc
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\dgroup\exp_default.txt"
DS, SS = idaapi.str2reg("ds"), idaapi.str2reg("ss")
out = []


def ranges(s, reg):
    rr = ida_segregs.sreg_range_t()
    res = []
    ea = s.start_ea
    while ea < s.end_ea and len(res) < 12:
        if not ida_segregs.get_sreg_range(rr, ea, reg):
            res.append("none@%X" % ea)
            break
        res.append("%X..%X v%X t%d" % (rr.start_ea, rr.end_ea, rr.val & 0xFFFF, rr.tag))
        ea = rr.end_ea
    return res


def run():
  for ea, reg, val in ((0x13D9C0, DS, idaapi.BADSEL), (0x13D9C0, DS, 0x7A32), (0x20000, SS, 0x7A32),
                       (0x4527F, SS, 0x7A32)):
      s = ida_segment.getseg(ea)
      out.append("== %s reg %d before %s" % (ida_segment.get_segm_name(s), reg, ranges(s, reg)))
      out.append("   defsr %X" % (ida_segregs.get_sreg(s.start_ea, reg) & 0xFFFF))
      ida_segregs.set_default_sreg_value(s, reg, val)
      out.append("   after set %X: %s" % (val & 0xFFFF, ranges(s, reg)))
      out.append("   get_sreg(%X)=%X" % (s.start_ea + 0x20, ida_segregs.get_sreg(s.start_ea + 0x20, reg) & 0xFFFF))
import traceback
try:
    run()
except Exception:
    out.append(traceback.format_exc())
open(OUT, "w").write("\n".join(out))
ida_loader.set_database_flag(ida_loader.DBFL_KILL)
idaapi.qexit(0)
