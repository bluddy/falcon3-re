"""Read-only (DBFL_KILL): no-return flags of 0x10B1C and its thunk, and the full disasm of 0x10B1C.
Output: analysis/s1/noret_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_name
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\noret_probe.json"
R = {}
try:
    tgt = ida_name.get_name_ea(idaapi.BADADDR, "jmp_loc_10b1c")
    R["thunk"] = tgt
    for ea in (0x10B1C, tgt):
        f = ida_funcs.get_func(ea)
        R["%X" % ea] = {"func": f and [f.start_ea, f.end_ea, idc.get_func_name(f.start_ea),
                                        bool(f.flags & ida_funcs.FUNC_NORET),
                                        bool(f.flags & ida_funcs.FUNC_NORET_PENDING)],
                        "disasm": [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(ea, (f.end_ea if f else ea + 16))],
                        "callers": len(list(idautils.CodeRefsTo(ea, 0)))}
    R["noret_funcs"] = [[ea, idc.get_func_name(ea)] for ea in idautils.Functions()
                        if ida_funcs.get_func(ea).flags & ida_funcs.FUNC_NORET]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
