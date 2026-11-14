"""Read-only (DBFL_KILL): how sub_15AFD covers 0x15E42 and who reaches the orphan 0x15EC2..0x16060
(HEAD's sub_15E42 game_state_setup_multi, 0x15E42..0x16060).  Output: analysis/s1/orphan15_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan15_probe.json"
R = {}
try:
    f = ida_funcs.get_func(0x15AFD)
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    R["chunks_15AFD"] = out
    R["flags_15AFD"] = f.flags
    R["heads_15E00"] = [[h, idc.generate_disasm_line(h, 0),
                         [[x.frm, x.type, idc.get_func_name(x.frm)] for x in idautils.XrefsTo(h, 0)]]
                        for h in idautils.Heads(0x15E00, 0x15EC8)]
    R["xrefs_in_orphan"] = [[h, [[x.frm, x.type, idc.get_func_name(x.frm)] for x in idautils.XrefsTo(h, 0)
                                 if not (0x15EC2 <= x.frm < 0x16060)]]
                            for h in idautils.Heads(0x15EC2, 0x16060)]
    R["xrefs_in_orphan"] = [r for r in R["xrefs_in_orphan"] if r[1]]
    R["ida_name_15E42"] = idc.get_name(0x15E42)
    R["ida_name_15EC2"] = idc.get_name(0x15EC2)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
