import json, traceback
import idaapi, idautils, idc, ida_funcs, ida_bytes, ida_segment, ida_xref
OUT = "C:/Users/ybarnoy/projects/falcon3/analysis/s1/probe_misc3.json"
R = {}
try:
    for lo, hi in ((0x127E40, 0x127E5A), (0x128A90, 0x128AA6)):
        R["%X" % lo] = {"bytes": idc.get_bytes(lo, hi - lo).hex(),
                        "heads": [["%X" % h, ida_bytes.get_item_size(h), "%X" % ida_bytes.get_flags(h), idc.generate_disasm_line(h, 0),
                                   [("%X" % x.frm, x.type) for x in idautils.XrefsTo(h, 0)][:6]] for h in idautils.Heads(lo, hi + 2)]}
    for sw in (0x127E4C, 0x128A9A):
        si = idaapi.get_switch_info(idc.prev_head(sw, 0)) if False else None
    # who uses the jump tables
    for t in (0x127E4C, 0x128A9A):
        R["xto_%X" % t] = [("%X" % x.frm, x.type, idc.generate_disasm_line(x.frm, 0)) for x in idautils.XrefsTo(t, 0)]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
