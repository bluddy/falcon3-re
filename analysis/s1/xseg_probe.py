"""Read-only (DBFL_KILL): every tail chunk whose segment differs from its owner's segment.
Output: analysis/s1/xseg_probe.json  [[owner, owner_name, owner_seg, lo, hi, chunk_seg, n_refs_in, prev_owner]]"""
import json
import idaapi, idc, idautils, ida_funcs, ida_segment
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\xseg_probe.json"
rows = []
for fs in idautils.Functions():
    f = ida_funcs.get_func(fs)
    so = ida_segment.getseg(fs)
    it = ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        c = it.chunk()
        sc = ida_segment.getseg(c.start_ea)
        if c.start_ea != f.start_ea and sc.start_ea != so.start_ea:
            p = idc.prev_head(c.start_ea, 0)
            pf = ida_funcs.get_func(p)
            rows.append([fs, idc.get_func_name(fs), ida_segment.get_segm_name(so), c.start_ea, c.end_ea,
                         ida_segment.get_segm_name(sc),
                         [[x.frm, x.type] for x in idautils.XrefsTo(c.start_ea, 0)],
                         [p, pf.start_ea if pf else None, idc.generate_disasm_line(p, 0)]])
        ok = it.next()
open(OUT, "w").write(json.dumps(rows))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
