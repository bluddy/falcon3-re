"""Read-only: full integrity diff vs function_bytes.json with context (DBFL_KILL).
Output: analysis/s1/integrity_detail.json"""
import json, traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_segment
ROOT = r"C:\Users\ybarnoy\projects\falcon3"
FB = ROOT + r"\analysis\ida_falconcd\function_bytes.json"
OUT = ROOT + r"\analysis\s1\integrity_detail.json"
R = {"missing": [], "span": [], "name": []}


def fdesc(f):
    if not f:
        return None
    return {"start": f.start_ea, "end": f.end_ea, "name": idc.get_func_name(f.start_ea),
            "tails": [[t.start_ea, t.end_ea] for t in idaapi.func_tail_iterator_t(f)] if False else
            [[a.start_ea, a.end_ea] for a in _chunks(f)]}


def _chunks(f):
    it = ida_funcs.func_tail_iterator_t(f)
    out = []
    ok = it.main()
    while ok:
        out.append(it.chunk())
        ok = it.next()
    return out


def item(ea):
    fl = ida_bytes.get_flags(ea)
    return {"code": ida_bytes.is_code(fl), "data": ida_bytes.is_data(fl), "head": ida_bytes.get_item_head(ea),
            "dis": idc.generate_disasm_line(ea, 0) if ida_bytes.is_code(fl) else None}


try:
    fb = json.loads(open(FB).read())
    for k, v in fb.items():
        ea, sz = v["ea"], v["size"]
        f = ida_funcs.get_func(ea)
        rec = {"key": k, "ea": ea, "size": sz, "want": v.get("name"),
               "seg": ida_segment.get_segm_name(ida_segment.getseg(ea)) if ida_segment.getseg(ea) else None}
        if not f:
            rec["item"] = item(ea)
            rec["fn_at_end"] = fdesc(ida_funcs.get_func(ea + sz - 1))
            R["missing"].append(rec)
            continue
        if f.start_ea != ea or f.end_ea - f.start_ea != sz:
            rec["live"] = fdesc(f)
            # functions living inside the recorded span
            inner = []
            x = ea
            while x < ea + sz:
                g = ida_funcs.get_func(x)
                if g and g.start_ea >= ea and (not inner or inner[-1]["start"] != g.start_ea):
                    inner.append({"start": g.start_ea, "end": g.end_ea, "name": idc.get_func_name(g.start_ea)})
                x = idc.next_head(x, ea + sz) if idc.next_head(x, ea + sz) != idaapi.BADADDR else ea + sz
            rec["inner"] = inner
            rec["prev_disasm"] = item(idc.prev_head(ea, 0))
            R["span"].append(rec)
        want = v.get("name")
        got = idc.get_func_name(ea) or ""
        if want and got != want:
            R["name"].append({"key": k, "ea": ea, "want": want, "got": got, "fstart": f.start_ea,
                              "name_at_ea": idc.get_name(ea)})
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
