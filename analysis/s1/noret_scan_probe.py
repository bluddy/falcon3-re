"""Read-only (DBFL_KILL): every FUNC_NORET function, whether it contains a ret/retf/iret, how its last
chunk ends, and how many callers have their flow cut after the call.  Output: analysis/s1/noret_scan.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_ua
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\noret_scan.json"
RETS = {"retn", "retf", "ret", "iret", "iretw", "retnw", "retfw"}
R = {"rows": []}
try:
    for fs in idautils.Functions():
        f = ida_funcs.get_func(fs)
        if not (f.flags & ida_funcs.FUNC_NORET):
            continue
        rets, last = 0, None
        it = ida_funcs.func_tail_iterator_t(f)
        ok = it.main()
        chunks = []
        while ok:
            c = it.chunk()
            chunks.append((c.start_ea, c.end_ea))
            ea = c.start_ea
            while ea < c.end_ea:
                if ida_bytes.is_code(ida_bytes.get_flags(ea)):
                    m = idc.print_insn_mnem(ea)
                    if m in RETS:
                        rets += 1
                    last = (ea, m)
                ea = idc.next_head(ea, c.end_ea)
                if ea == idaapi.BADADDR:
                    break
            ok = it.next()
        calls = []
        for x in idautils.XrefsTo(fs, 0):
            if not x.iscode:
                continue
            m = idc.print_insn_mnem(x.frm)
            if not m.startswith("call"):
                continue
            nx = x.frm + ida_bytes.get_item_size(x.frm)
            fl = ida_bytes.get_flags(nx)
            nf = ida_funcs.get_func(nx)
            cf = ida_funcs.get_func(x.frm)
            calls.append({"frm": x.frm, "cut": not ida_bytes.is_flow(fl), "next_code": bool(ida_bytes.is_code(fl)),
                          "next_owned": bool(nf), "same_func": bool(nf and cf and nf.start_ea == cf.start_ea)})
        R["rows"].append({"ea": fs, "name": idc.get_func_name(fs), "size": f.end_ea - f.start_ea, "chunks": len(chunks),
                          "rets": rets, "last": [hex(last[0]), last[1]] if last else None,
                          "calls": len(calls), "cut": sum(c["cut"] for c in calls),
                          "cut_orphan": sum(1 for c in calls if c["cut"] and (not c["next_owned"] or not c["same_func"]))})
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
