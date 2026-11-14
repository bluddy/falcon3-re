"""Read-only (DBFL_KILL): facts for tools/plan_rebase_fixes.py.
 * every cross-segment tail chunk: owner, bounds, code xrefs into each head of the chunk from outside it
   (with the function owning the source, if any), and whether the bytes are code heads end to end
 * 0x15AFD and the function-less code run 0x15BEB..0x15EAB (switch tail reached by jmp loc_15BEB)
 * r06_trig_accum_6de83 (0x6DE83) and the code run 0x6DF27.. up to sub_6DFCB
 * 0x161945..0x161978 (target of far jmp 0x2C48A, byte at 0x161945 undefined)
 * the R06 head 0x6CD90..0x6CDA8 item states
Output: analysis/s1/rebase_plan_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_segment
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\rebase_plan_probe.json"
R = {}


def chunks(f):
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    return out


def items(lo, hi):
    out, ea = [], lo
    while ea < hi:
        fl = ida_bytes.get_flags(ea)
        h = ida_bytes.get_item_head(ea)
        sz = ida_bytes.get_item_size(h)
        out.append([ea, "C" if ida_bytes.is_code(fl) else "D" if ida_bytes.is_data(fl) else "U", h, sz])
        ea = h + sz if h + sz > ea else ea + 1
    return out


def inrefs(lo, hi):
    out = []
    for h in idautils.Heads(lo, hi):
        for x in idautils.XrefsTo(h, 0):
            if x.iscode and not (lo <= x.frm < hi):
                f = ida_funcs.get_func(x.frm)
                out.append([h, x.frm, x.type, f.start_ea if f else None])
    return out


try:
    rows = []
    for fs in idautils.Functions():
        f = ida_funcs.get_func(fs)
        so = ida_segment.getseg(fs).start_ea
        for lo, hi in chunks(f):
            if lo != fs and ida_segment.getseg(lo).start_ea != so:
                rows.append({"owner": fs, "lo": lo, "hi": hi,
                             "seg": ida_segment.get_segm_name(ida_segment.getseg(lo)),
                             "all_code": all(t == "C" for _, t, _, _ in items(lo, hi)),
                             "inrefs": inrefs(lo, hi)})
    R["xseg"] = rows
    f = ida_funcs.get_func(0x15AFD)
    R["15AFD"] = {"chunks": chunks(f), "name": idc.get_func_name(0x15AFD),
                  "run_items": [i for i in items(0x15BEB, 0x15EAB) if i[1] != "C"],
                  "run_funcs": [[x, ida_funcs.get_func(x).start_ea] for x in idautils.Heads(0x15BEB, 0x15EAB)
                                if ida_funcs.get_func(x)][:5],
                  "inrefs": inrefs(0x15BEB, 0x15EAB),
                  "at_15EAB": [idc.get_func_name(0x15EAB), idc.generate_disasm_line(0x15EAB, 0),
                               ida_funcs.get_func(0x15EAB).start_ea if ida_funcs.get_func(0x15EAB) else None],
                  "before": [idc.prev_head(0x15BEB, 0), idc.generate_disasm_line(idc.prev_head(0x15BEB, 0), 0)]}
    f = ida_funcs.get_func(0x6DE83)
    R["6DE83"] = {"chunks": chunks(f), "name": idc.get_func_name(0x6DE83),
                  "run_items": [i for i in items(0x6DF27, 0x6DFCB) if i[1] != "C"],
                  "run_funcs": [x for x in idautils.Heads(0x6DF27, 0x6DFCB) if ida_funcs.get_func(x)][:5],
                  "last": [idc.prev_head(0x6DFCB, 0), idc.generate_disasm_line(idc.prev_head(0x6DFCB, 0), 0)],
                  "f6DFCB": [ida_funcs.get_func(0x6DFCB).start_ea, ida_funcs.get_func(0x6DFCB).end_ea]}
    R["161945"] = {"items": items(0x161945, 0x161978),
                   "dis": [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(0x161945, 0x161978)],
                   "refs_161945": [[x.frm, x.type] for x in idautils.XrefsTo(0x161945, 0)],
                   "f": [idc.get_func_name(0x161946)], "next_f": idc.get_func_name(0x161978)}
    R["6CD90"] = {"items": items(0x6CD90, 0x6CDA8),
                  "f6CD29": [ida_funcs.get_func(0x6CD29).start_ea, ida_funcs.get_func(0x6CD29).end_ea]}
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
