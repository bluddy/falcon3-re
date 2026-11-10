"""Read-only (DBFL_KILL): every function chunk whose last instruction flows into the next byte
(fall-through out of the chunk).  Classifies the target: in no function (orphan continuation),
in another function (fall-in), or own chunk.  Output: analysis/s1/fallout_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\fallout_probe.json"
R = {"orphan": [], "fall_in": []}
try:
    for fea in idautils.Functions():
        f = ida_funcs.get_func(fea)
        it = ida_funcs.func_tail_iterator_t(f)
        ok = it.main()
        while ok:
            c = it.chunk()
            end = c.end_ea
            ok = it.next()
            fl = ida_bytes.get_flags(end)
            if not (ida_bytes.is_code(fl) and ida_bytes.is_flow(fl)):
                continue
            g = ida_funcs.get_func(end)
            last = idc.prev_head(end, c.start_ea)
            row = {"func": fea, "name": idc.get_func_name(fea), "chunk": [c.start_ea, end],
                   "last": [last, idc.generate_disasm_line(last, 0)],
                   "next": idc.generate_disasm_line(end, 0)}
            if g is None:
                # extent of the orphan code run: consecutive code heads outside any function
                ea = end
                while ida_bytes.is_code(ida_bytes.get_flags(ea)) and not ida_funcs.get_func(ea):
                    ea = idc.next_head(ea, idaapi.BADADDR)
                row["orphan_to"] = ea
                row["orphan_last"] = idc.generate_disasm_line(idc.prev_head(ea, end), 0)
                R["orphan"].append(row)
            elif g.start_ea != fea:
                row["into"] = [g.start_ea, idc.get_func_name(g.start_ea)]
                R["fall_in"].append(row)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
