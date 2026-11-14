"""Read-only (DBFL_KILL): why 0x2703F / 0x322E5 / 0x2FD42 end early (finding 124 re-baseline review).
Per function: chunks, flags, last heads; per callee before the cut: NORET flag + its own exits
(ret/retf/jmp-out/call-noret) so a wrong NORET can be told from a real one.
Output: analysis/s1/noret2_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_ua
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\noret2_probe.json"
R = {}


def chunks(f):
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    return out


def exits(f):
    """terminal instructions of f: ret*, and calls into NORET functions"""
    rows = []
    for lo, hi in chunks(f):
        for h in idautils.Heads(lo, hi):
            m = idc.print_insn_mnem(h)
            if m.startswith("ret") or m == "iret":
                rows.append([h, idc.generate_disasm_line(h, 0)])
            elif m.startswith("call"):
                for t in idautils.CodeRefsFrom(h, 0):
                    g = ida_funcs.get_func(t)
                    if g and g.flags & ida_funcs.FUNC_NORET and g.start_ea != f.start_ea:
                        rows.append([h, idc.generate_disasm_line(h, 0), "noret", g.start_ea])
    return rows


try:
    for ea, cut in ((0x2703F, 0x27042), (0x322E5, 0x32388), (0x2FD42, 0x2FEC1), (0x38C91, None),
                    (0x4F7B8, None), (0x3F700, 0x3F717), (0x3F788, None)):
        f = ida_funcs.get_func(ea)
        row = {"name": idc.get_func_name(ea), "chunks": f and chunks(f),
               "noret": bool(f and f.flags & ida_funcs.FUNC_NORET), "flags": f and f.flags,
               "exits": f and exits(f)[:30]}
        if cut:
            row["before_cut"] = [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(cut - 12, cut + 12)]
            prev = idc.prev_head(cut, 0)
            row["cut_prev_targets"] = []
            for t in idautils.CodeRefsFrom(prev, 0):
                g = ida_funcs.get_func(t)
                row["cut_prev_targets"].append([t, idc.get_func_name(t), bool(g and g.flags & ida_funcs.FUNC_NORET),
                                                g and exits(g)[:20]])
        R["%X" % ea] = row
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
