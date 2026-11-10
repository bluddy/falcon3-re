"""Experiment (copy only): after a SR_user entry DS, does IDA's reanalysis
recompute the inner auto ranges (pop ds / mov ax,ds..mov ds,ax)?"""
import idaapi, ida_segregs, ida_auto, ida_segment, ida_funcs, idautils, idc, ida_loader
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\dgroup\exp_prop.txt"
DS = idaapi.str2reg("ds")
out = []


def ranges(fs):
    f = ida_funcs.get_func(fs)
    rr = ida_segregs.sreg_range_t()
    res = []
    ea = fs
    while ea < f.end_ea:
        ida_segregs.get_sreg_range(rr, ea, DS)
        res.append("%X..%X v%X t%d" % (rr.start_ea, rr.end_ea, rr.val & 0xFFFF, rr.tag))
        ea = rr.end_ea
    return res


sel = ida_segment.setup_selector(0x7A32)
for fs in (0x4E90E, 0x10A0C4, 0x31EBF, 0x4D544):
    out.append("== %X before %s" % (fs, ranges(fs)))
    ida_segregs.split_sreg_range(fs, DS, sel, ida_segregs.SR_user)
    out.append("   after split %s" % ranges(fs))
nf = ida_funcs.get_func_qty()
ida_auto.auto_wait()
for fs in (0x4E90E, 0x10A0C4, 0x31EBF, 0x4D544):
    out.append("== %X after auto_wait %s" % (fs, ranges(fs)))
for fs in (0x4E90E, 0x10A0C4, 0x31EBF, 0x4D544):
    f = ida_funcs.get_func(fs)
    ida_auto.plan_range(f.start_ea, f.end_ea)
ida_auto.auto_wait()
for fs in (0x4E90E, 0x10A0C4, 0x31EBF, 0x4D544):
    out.append("== %X after plan_range %s" % (fs, ranges(fs)))
out.append("funcs %d -> %d" % (nf, ida_funcs.get_func_qty()))
open(OUT, "w").write("\n".join(out))
ida_loader.set_database_flag(ida_loader.DBFL_KILL)
idaapi.qexit(0)
