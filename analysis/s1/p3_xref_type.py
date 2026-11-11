"""
p3_xref_type.py  —  check xref types (flow vs branch) for the 17 failing P3 entries.
Run: idat -A -S"analysis/s1/p3_xref_type.py" analysis/ida_falconcd/FALCONCD.EXE.i64
"""
import idautils, idc, ida_funcs, ida_bytes, json, traceback
from pathlib import Path

# idc xref type constants
fl_F  = 17  # flow (sequential fall-through)
fl_jN = 18  # ordinary jump
fl_cn = 19  # call
# Type names for display
TYPE_NAMES = {17: "flow", 18: "jmp", 19: "call", 20: "callF"}

SPLITS = [
    (0x20AC1, 0x20B29),
    (0x28CA1, 0x28CA4),
    (0x33443, 0x3352A),
    (0x39CE0, 0x39D02),
    (0x3C00C, 0x3C03D),
    (0x3E8C5, 0x3E8D2),
    (0x3E962, 0x3E96F),
    (0x3F62C, 0x3F62F),
    (0x3FD89, 0x3FD9A),
    (0x42AFA, 0x42C31),
    (0x42E31, 0x42E37),
    (0x49C67, 0x49C80),
    (0x4A4F6, 0x4A505),
    (0x4D3EC, 0x4D459),
    (0x4EE65, 0x4EE82),
    (0x4F7F0, 0x4F84B),
    (0x6E32A, 0x6E343),
    (0x13DB5D, 0x13DB5E),
    (0x13DC09, 0x13DC0A),
]

OUT = Path("analysis/s1/p3_xref_type.json")
LOG = Path("analysis/s1/p3_xref_type.log")

results = []
log = []

try:
    for ea, at in SPLITS:
        f = ida_funcs.get_func(at)
        owner_ok = f and f.start_ea == ea
        inner_xrefs = []
        for xr in idautils.XrefsTo(at, 0):
            if not xr.iscode:
                continue
            xf = ida_funcs.get_func(xr.frm)
            if xf and xf.start_ea == ea:
                m = idc.print_insn_mnem(xr.frm)
                isz = ida_bytes.get_item_size(xr.frm)
                is_flow = (xr.frm + isz == at)  # instruction immediately precedes 'at'
                inner_xrefs.append({
                    "from": hex(xr.frm), "mnem": m,
                    "type_num": xr.type, "type_name": TYPE_NAMES.get(xr.type, str(xr.type)),
                    "insn_size": isz, "is_flow": is_flow
                })
        only_flow = all(x["is_flow"] for x in inner_xrefs)
        has_branch = any(not x["is_flow"] for x in inner_xrefs)
        verdict = "OK_FLOW" if (only_flow and not has_branch) else ("MIXED" if has_branch and inner_xrefs else "OK_NOCROSSREF")
        if not inner_xrefs:
            verdict = "OK_CALL_ONLY"
        log.append("%s  0x%X at 0x%X  owner=%s  xrefs=%s" % (verdict, ea, at, owner_ok, inner_xrefs))
        results.append({"owner": hex(ea), "at": hex(at), "verdict": verdict,
                        "owner_in_idb": owner_ok, "inner_xrefs": inner_xrefs})

    OUT.write_text(json.dumps(results, indent=1))
    LOG.write_text("\n".join(log))
except Exception:
    LOG.write_text(traceback.format_exc())

import idaapi; idaapi.qexit(0)
