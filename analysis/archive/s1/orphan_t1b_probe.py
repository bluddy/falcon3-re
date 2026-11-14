"""Plan probe (COPY, DBFL_KILL): the 10 call targets add_func(ea) refused.  For each, find the end of its orphan
run (or the next call target inside the run) and try add_func(ea, end).  Output: analysis/s1/orphan_t1b.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_ua
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan_t1b.json"
FAILED = [0x129F7, 0x1617C, 0x162DF, 0x6DFF0, 0x6E16E, 0x106EE2, 0x108430, 0x10931E, 0x109445, 0x10CE30]


def run_end(ea):
    """end of the orphan code run that starts at ea"""
    a = ea
    while True:
        h = ida_bytes.get_item_head(a)
        if not ida_bytes.is_code(ida_bytes.get_flags(h)) or (ida_funcs.get_func(h) and h != ea):
            return h
        a = h + max(ida_bytes.get_item_size(h), 1)


R = {"rows": []}
try:
    ends = {}
    for ea in FAILED:
        e = run_end(ea)
        nxt = [t for t in FAILED if ea < t < e]
        ends[ea] = min(nxt) if nxt else e
    for ea in FAILED:
        row = {"ea": ea, "end": ends[ea], "size": ends[ea] - ea,
               "first": idc.generate_disasm_line(ea, 0),
               "last": idc.generate_disasm_line(idc.prev_head(ends[ea], ea), 0),
               "owner_at_end": (lambda g: g and g.start_ea)(ida_funcs.get_func(ends[ea]))}
        ok = ida_funcs.add_func(ea, ends[ea])
        row["ok"] = bool(ok)
        if ok:
            f = ida_funcs.get_func(ea)
            row["got_end"] = f.end_ea
            row["flags"] = f.flags
        R["rows"].append(row)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
