"""Read-only (DBFL_KILL): for non-thunk far tails, segment of owner and which items (anywhere) branch into the chunk.
Output: analysis/s1/fartail_probe2.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_segment
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\fartail_probe2.json"
OWNERS = [0x4E109, 0x4E14C, 0x13DC5E, 0x13DD40, 0x13DDE2, 0x13DE3A, 0x13DE82]
R = {}
try:
    for o in OWNERS:
        f = ida_funcs.get_func(o)
        s = ida_segment.getseg(o)
        ch, it = [], ida_funcs.func_tail_iterator_t(f)
        ok = it.main()
        while ok:
            c = it.chunk()
            refs = []
            for h in idautils.Heads(c.start_ea, c.end_ea):
                for x in idautils.XrefsTo(h, 0):
                    if not (c.start_ea <= x.frm < c.end_ea):
                        refs.append([h, x.frm, x.type, idc.get_func_name(x.frm),
                                     ida_segment.get_segm_name(ida_segment.getseg(x.frm))])
            ch.append([c.start_ea, c.end_ea, ida_segment.get_segm_name(ida_segment.getseg(c.start_ea)), refs])
            ok = it.next()
        R["%X" % o] = {"seg": ida_segment.get_segm_name(s), "seg_lo": s.start_ea, "seg_hi": s.end_ea,
                       "sel": s.sel, "chunks": ch,
                       "dis": [[h, idc.generate_disasm_line(h, 0)] for h in idautils.Heads(f.start_ea, f.end_ea)]}
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
