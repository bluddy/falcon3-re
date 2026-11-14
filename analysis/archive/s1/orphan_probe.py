"""Read-only (DBFL_KILL): the orphaned jmp at 0x67BA3 (was the last insn of sub_67AE1 at HEAD).
Output: analysis/s1/orphan_probe.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orphan_probe.json"
R = {}
try:
    R["heads"] = [[h, idc.generate_disasm_line(h, 0), (lambda f: f and [f.start_ea, f.end_ea])(ida_funcs.get_func(h)),
                   [[x.frm, x.type, idc.get_func_name(x.frm)] for x in idautils.XrefsTo(h, 0)]]
                  for h in idautils.Heads(0x67B80, 0x67BB0)]
    f = ida_funcs.get_func(0x67AE1)
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append([it.chunk().start_ea, it.chunk().end_ea])
        ok = it.next()
    R["chunks_67AE1"] = out
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R, indent=1))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
