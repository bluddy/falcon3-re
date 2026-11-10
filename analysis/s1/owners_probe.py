"""Read-only (DBFL_KILL): the existing functions that sit inside the flow-walked span of each seed.
Output: analysis/s1/owners.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_name
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\owners.json"
OWN = [0x10843D, 0x106EEC, 0x10CFA6, 0x109519]
R = {"owners": []}
try:
    for ea in OWN:
        f = ida_funcs.get_func(ea)
        row = {"ea": ea, "name": idaapi.get_name(ea), "user_name": bool(ida_name.is_uname(idaapi.get_name(ea))),
               "start": f.start_ea, "end": f.end_ea, "flags": f.flags,
               "xrefs_to": [[x.frm, x.type] for x in idautils.XrefsTo(ea, 0)][:10],
               "prev_head": idc.generate_disasm_line(idc.prev_head(ea), 0), "prev_head_ea": idc.prev_head(ea),
               "prev_func": (lambda g: g and [g.start_ea, g.end_ea])(ida_funcs.get_func(idc.prev_head(ea))),
               "first": [idc.generate_disasm_line(a, 0) for a in (ea,)],
               "cmt": idc.get_func_cmt(ea, 0)}
        R["owners"].append(row)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
