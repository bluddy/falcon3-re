"""Plan probe (run on a COPY, DBFL_KILL): register call-reached orphan code heads as functions, in rounds
(targets of calls from code, landing on a code head that belongs to no function).  Reports each new function
(ea, end, last insn, chunk count), the orphan bytes left, and any change to a pre-existing function.
Output: analysis/s1/orphan_t1.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_segment
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan_t1.json"
RETS = {"retn", "retf", "iret", "iretw", "retnw", "retfw"}
CALLS = (16, 17)  # fl_CF, fl_CN


def chunks(ea):
    f = ida_funcs.get_func(ea)
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    return sorted(out)


def table():
    return {fs: (idaapi.get_name(fs), chunks(fs)) for fs in idautils.Functions()}


def seeds():
    out = set()
    for si in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(si)
        if s.type != ida_segment.SEG_CODE:
            continue
        ea = s.start_ea
        while ea < s.end_ea:
            h = ida_bytes.get_item_head(ea)
            sz = max(ida_bytes.get_item_size(h), 1)
            if ida_bytes.is_code(ida_bytes.get_flags(h)) and not ida_funcs.get_func(h):
                for x in idautils.XrefsTo(h, 0):
                    if x.type in CALLS and ida_bytes.is_code(ida_bytes.get_flags(x.frm)) and ida_funcs.get_func(x.frm):
                        out.add(h)
                        break
            ea = h + sz
    return sorted(out)


R = {"rounds": [], "new": []}
try:
    before = table()
    for rnd in range(8):
        ss = seeds()
        if not ss:
            break
        row = {"seeds": ss, "added": [], "failed": []}
        for ea in ss:
            if ida_funcs.get_func(ea):
                continue
            if ida_funcs.add_func(ea):
                f = ida_funcs.get_func(ea)
                last = idc.prev_head(f.end_ea, ea)
                row["added"].append([ea, f.end_ea, idc.print_insn_mnem(last), len(chunks(ea))])
            else:
                row["failed"].append(ea)
        R["rounds"].append(row)
        if not row["added"]:
            break
    after = table()
    R["changed_existing"] = [[k, before[k], after.get(k)] for k in before if before[k] != after.get(k)]
    R["new"] = sorted(k for k in after if k not in before)
    R["n_before"], R["n_after"] = len(before), len(after)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
