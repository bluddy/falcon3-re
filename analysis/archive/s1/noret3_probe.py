"""Read-only (DBFL_KILL): suspicious no-return flags and the truncations they cause (finding 124).
  noret_with_ret : FUNC_NORET functions that contain a ret/retf/iret (a real no-return never returns)
  noret_calls    : for every NORET function, its exits: rets, calls to other NORET functions
  truncated      : function chunks whose last insn is a call to a NORET function or that end with flow
                   into code in no function, with the orphan run up to the first ret/jmp
Output: analysis/s1/noret3_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\noret3_probe.json"
R = {"noret": [], "truncated": []}


def chunks(f):
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    return out


def noret(ea):
    g = ida_funcs.get_func(ea)
    return bool(g and g.start_ea == ea and g.flags & ida_funcs.FUNC_NORET)


try:
    for fea in idautils.Functions():
        f = ida_funcs.get_func(fea)
        if f.flags & ida_funcs.FUNC_NORET:
            rets, nrcalls = [], []
            for lo, hi in chunks(f):
                for h in idautils.Heads(lo, hi):
                    m = idc.print_insn_mnem(h)
                    if m.startswith("ret") or m == "iret":
                        rets.append(h)
                    elif m.startswith("call"):
                        nrcalls += [[h, t] for t in idautils.CodeRefsFrom(h, 0) if noret(t)]
            R["noret"].append({"ea": fea, "name": idc.get_func_name(fea), "rets": rets, "noret_calls": nrcalls,
                               "callers": len([x for x in idautils.CodeRefsTo(fea, 0)])})
        for lo, hi in chunks(f):
            last = idc.prev_head(hi, lo)
            fl = ida_bytes.get_flags(hi)
            if not ida_bytes.is_code(fl) or ida_funcs.get_func(hi):
                continue
            m = idc.print_insn_mnem(last)
            tg = [t for t in idautils.CodeRefsFrom(last, 0) if t != hi]
            if not (ida_bytes.is_flow(fl) or (m.startswith("call") and any(noret(t) for t in tg))):
                continue
            ea, run = hi, []
            while ida_bytes.is_code(ida_bytes.get_flags(ea)) and not ida_funcs.get_func(ea) and len(run) < 400:
                run.append(ea)
                mm = idc.print_insn_mnem(ea)
                if mm.startswith("ret") or mm == "iret" or mm == "jmp" or mm.startswith("jmp"):
                    ea = idc.next_head(ea, idaapi.BADADDR)
                    break
                ea = idc.next_head(ea, idaapi.BADADDR)
            R["truncated"].append({"func": fea, "name": idc.get_func_name(fea), "chunk": [lo, hi],
                                   "last": [last, idc.generate_disasm_line(last, 0)],
                                   "last_noret_targets": [[t, idc.get_func_name(t)] for t in tg if noret(t)],
                                   "flow": bool(ida_bytes.is_flow(fl)), "run_end": ea,
                                   "run_last": idc.generate_disasm_line(run[-1], 0) if run else None,
                                   "run_inrefs": [[x.frm, x.type] for h in run for x in idautils.XrefsTo(h, 0)
                                                  if not (hi <= x.frm < ea) and x.frm != last]})
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
