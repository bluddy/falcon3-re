"""Read-only (DBFL_KILL): the 0x20000-alias far tails - functions/orphan runs around each chunk, owner of the
flow-in instruction, and whether the owner-relative alias (chunk+0x20000) is inside the owner.
Output: analysis/s1/alias_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\alias_probe.json"
R = {}
try:
    for lo, hi in ((0x2E100, 0x2E300), (0x11DA00, 0x11E1B0)):
        rows = []
        ea = lo
        while ea < hi:
            fl = ida_bytes.get_flags(ea)
            f = ida_funcs.get_func(ea)
            fs = ida_funcs.get_fchunk(ea)
            rows.append([ea, "C" if ida_bytes.is_code(fl) else "D" if ida_bytes.is_data(fl) else "U",
                         idc.get_func_name(ea) or "", fs.start_ea if fs else None,
                         bool(fs and f and fs.start_ea != f.start_ea), idc.generate_disasm_line(ea, 0)])
            nx = idc.next_head(ea, hi)
            if nx == idaapi.BADADDR or nx <= ea:
                break
            ea = nx
        R["%X" % lo] = rows
    R["funcs"] = [[f, ida_funcs.get_func(f).end_ea, idc.get_func_name(f)] for f in idautils.Functions(0x11D900, 0x11E700)]
    R["funcs_2E"] = [[f, ida_funcs.get_func(f).end_ea, idc.get_func_name(f)] for f in idautils.Functions(0x2E000, 0x2E400)]
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
