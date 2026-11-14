"""Read-only (DBFL_KILL): every function's IDB name and name provenance.
Output: analysis/s1/names_live2.json  [[start, end, name, user, dummy, lib]]"""
import json
import idaapi, idautils, idc, ida_bytes, ida_funcs
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\names_live2.json"
rows = []
for ea in idautils.Functions():
    f = ida_funcs.get_func(ea)
    fl = ida_bytes.get_flags(ea)
    rows.append([ea, f.end_ea, idc.get_func_name(ea), bool(ida_bytes.has_user_name(fl)),
                 bool(ida_bytes.has_dummy_name(fl)), bool(f.flags & ida_funcs.FUNC_LIB)])
open(OUT, "w").write(json.dumps(rows))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
