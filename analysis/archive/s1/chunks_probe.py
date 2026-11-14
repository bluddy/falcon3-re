"""Read-only (DBFL_KILL): chunk lists of every function the rebase fixes touch, plus the code-head
class of every byte range the fixes read or write (for tools/plan_rebase_fixes.py).
Input eas: analysis/s1/chunks_probe_in.json  {"funcs": [ea...], "ranges": [[lo, hi]...]}
Output:    analysis/s1/chunks_probe.json     {"funcs": {ea: [[lo, hi]...] | null}, "ranges": {lo: [[head, cls, size, func]...]}}"""
import json, traceback
import idaapi, idc, ida_funcs, ida_bytes
IN = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\chunks_probe_in.json"
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\chunks_probe.json"
R = {"funcs": {}, "ranges": {}}
try:
    doc = json.load(open(IN))
    for ea in doc["funcs"]:
        f = ida_funcs.get_func(ea)
        if not f or f.start_ea != ea:
            R["funcs"][str(ea)] = None
            continue
        out, it = [], ida_funcs.func_tail_iterator_t(f)
        ok = it.main()
        while ok:
            out.append([it.chunk().start_ea, it.chunk().end_ea])
            ok = it.next()
        R["funcs"][str(ea)] = sorted(out)
    for lo, hi in doc["ranges"]:
        rows, ea = [], lo
        while ea < hi:
            fl = ida_bytes.get_flags(ea)
            h = ida_bytes.get_item_head(ea)
            sz = max(1, ida_bytes.get_item_size(h))
            f = ida_funcs.get_func(ea)
            rows.append([h, "C" if ida_bytes.is_code(fl) else "D" if ida_bytes.is_data(fl) else "U", sz,
                         f.start_ea if f else None])
            ea = h + sz if h + sz > ea else ea + 1
        R["ranges"][str(lo)] = rows
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
