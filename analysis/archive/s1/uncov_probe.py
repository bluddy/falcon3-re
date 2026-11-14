"""Read-only (DBFL_KILL): bytes HEAD had inside a function that the live IDB leaves in none.
Per span: heads (class, flow-from-prev, disasm, owner), and for the instruction just before the
span its call target's NORET flag.  Input: analysis/s1/uncov_probe_in.json [[lo, hi]...]
Output: analysis/s1/uncov_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
IN = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\uncov_probe_in.json"
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\uncov_probe.json"
R = []
try:
    for lo, hi in json.load(open(IN)):
        prev = idc.prev_head(lo, 0)
        pf = ida_funcs.get_func(prev)
        tgt = [x for x in idautils.CodeRefsFrom(prev, 0)]
        rows = []
        ea = lo
        while ea < hi:
            fl = ida_bytes.get_flags(ea)
            h = ida_bytes.get_item_head(ea)
            sz = max(1, ida_bytes.get_item_size(h))
            f = ida_funcs.get_func(ea)
            rows.append([h, "C" if ida_bytes.is_code(fl) else "D" if ida_bytes.is_data(fl) else "U",
                         bool(ida_bytes.is_flow(fl)), idc.generate_disasm_line(h, 0), f.start_ea if f else None,
                         [[x.frm, x.type] for x in idautils.XrefsTo(h, 0) if not (lo <= x.frm < hi)]])
            ea = h + sz if h + sz > ea else ea + 1
        R.append({"lo": lo, "hi": hi,
                  "prev": [prev, idc.generate_disasm_line(prev, 0), pf.start_ea if pf else None],
                  "prev_targets": [[t, idc.get_func_name(t),
                                    bool(ida_funcs.get_func(t) and ida_funcs.get_func(t).flags & ida_funcs.FUNC_NORET)]
                                   for t in tgt],
                  "after": [hi, idc.generate_disasm_line(hi, 0),
                            (lambda g: g and g.start_ea)(ida_funcs.get_func(hi))],
                  "heads": rows})
except Exception:
    R = {"error": traceback.format_exc()}
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
