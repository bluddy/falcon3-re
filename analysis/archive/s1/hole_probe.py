"""Read-only (DBFL_KILL): code around the retired register holes 0x161B10 and 0x6DF27.
Output: analysis/s1/hole_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\hole_probe.json"
R = {}
try:
    for lo, hi in [(0x161AF0, 0x161B40), (0x6DF10, 0x6DF40)]:
        f = ida_funcs.get_func(lo + 0x20)
        R["%X" % lo] = {"func": [f.start_ea, f.end_ea, idc.get_func_name(f.start_ea)] if f else None,
                        "heads": [[h, idc.generate_disasm_line(h, 0),
                                   [[x.frm, x.type] for x in idautils.XrefsTo(h, 0) if x.iscode]]
                                  for h in idautils.Heads(lo, hi)]}
    f = ida_funcs.get_func(0x161B10)
    R["refs_161B10"] = [[x.frm, x.type, idc.get_func_name(x.frm)] for x in idautils.XrefsTo(0x161B10, 0)]
    R["tail_161B10"] = [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(f.end_ea - 12, f.end_ea + 4)]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
