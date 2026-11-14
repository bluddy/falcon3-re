"""Probe-copy experiment: does defining selector 0x39C1 -> para of R29_29C1s redirect far operand 39C1:xxxx?"""
import json, traceback
import idaapi, idautils, idc, ida_bytes, ida_segment, ida_ua, ida_xref, ida_funcs
OUT = "C:/Users/ybarnoy/projects/falcon3/analysis/s1/exp_sel.txt"
L = []
def refs(ea):
    return [("%X" % x.to, x.type, x.user) for x in idautils.XrefsFrom(ea, ida_xref.XREF_FAR) if x.iscode]
try:
    ea = 0x11CF5E
    L.append("before %s refs=%s" % (idc.generate_disasm_line(ea, 0), refs(ea)))
    L.append("sel2para(0x39C1)=%X find_selector=%X" % (ida_segment.sel2para(0x39C1), ida_segment.find_selector(0x39C1)))
    ok = ida_segment.set_selector(0x39C1, 0x127ED)
    L.append("set_selector -> %s sel2para=%X" % (ok, ida_segment.sel2para(0x39C1)))
    L.append("no-reanalysis %s refs=%s" % (idc.generate_disasm_line(ea, 0), refs(ea)))
    # re-create the instruction (this is what a repair would do), no auto_wait
    f = ida_funcs.get_func(ea)
    ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 5)
    n = ida_ua.create_insn(ea)
    L.append("recreate n=%d %s refs=%s infn=%s" % (n, idc.generate_disasm_line(ea, 0), refs(ea), ida_funcs.get_func(ea) is not None))
    # R05 code that uses seg 0x2E10? sanity: a resident caller with seg 39C1?
    L.append("op value %X" % idc.get_operand_value(ea, 0))
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
