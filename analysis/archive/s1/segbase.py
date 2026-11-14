"""Read-only: segment table with bases; for each mid-body caller, IP decomposition."""
import json, traceback
import idaapi, idc, ida_segment, ida_ua, ida_idp, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\segbase.json"
R = {"segs": [], "calls": []}
try:
    for s in idautils.Segments():
        g = ida_segment.getseg(s)
        R["segs"].append([ida_segment.get_segm_name(g), g.start_ea, g.end_ea, ida_segment.get_segm_base(g), g.sel, g.bitness])
    T = json.load(open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\mid_detail.json"))["targets"]
    for t in T:
        for c in t["callers"]:
            ea = c["ea"]
            insn = ida_ua.insn_t(); ida_ua.decode_insn(insn, ea)
            op = insn.ops[0]
            g = ida_segment.getseg(ea)
            R["calls"].append({"ea": ea, "t": t["t"], "optype": op.type, "addr": op.addr, "seg_val": op.specval if op.type == idaapi.o_far else None,
                               "cseg": ida_segment.get_segm_name(g), "cbase": ida_segment.get_segm_base(g),
                               "tseg": ida_segment.get_segm_name(ida_segment.getseg(t["t"])),
                               "fixup": idc.get_fixup_target_type(ea + 1) if hasattr(idc, "get_fixup_target_type") else None,
                               "bytes": (idc.get_bytes(ea, insn.size) or b"").hex()})
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
