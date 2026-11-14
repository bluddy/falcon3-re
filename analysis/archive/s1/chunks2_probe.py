"""Read-only (DBFL_KILL): chunks + NORET flag of the S1c-2 repair targets, and whether each planned
extension [end, new_end) is code in no function.  Output: analysis/s1/chunks2_probe.json"""
import json, traceback
import idaapi, idc, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\chunks2_probe.json"
EXT = {0x15AFD: 0x16060, 0x2703F: 0x27051, 0x322E5: 0x32393, 0x2FD42: 0x2FEC5, 0x3F700: 0x3F718}
NORET = [0x4F7B8, 0x38C91, 0x2FD42, 0x322E5, 0x3F700]
R = {}
try:
    for ea in sorted(set(EXT) | set(NORET)):
        f = ida_funcs.get_func(ea)
        out, it = [], ida_funcs.func_tail_iterator_t(f)
        ok = it.main()
        while ok:
            out.append([it.chunk().start_ea, it.chunk().end_ea])
            ok = it.next()
        row = {"name": idc.get_func_name(ea), "chunks": out, "noret": bool(f.flags & ida_funcs.FUNC_NORET),
               "end": f.end_ea}
        if ea in EXT:
            bad = [a for a in range(f.end_ea, EXT[ea]) if ida_funcs.get_func(a) or
                   not ida_bytes.is_code(ida_bytes.get_flags(ida_bytes.get_item_head(a)))]
            last = idc.prev_head(EXT[ea], f.end_ea)
            row["ext"] = {"to": EXT[ea], "bad": bad[:10], "last": idc.generate_disasm_line(last, 0),
                          "next_func": (lambda g: g and g.start_ea)(ida_funcs.get_func(EXT[ea]))}
        R["%X" % ea] = row
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
