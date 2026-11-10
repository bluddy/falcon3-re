"""Read-only (DBFL_KILL): decode check of hole 0x6DF27 (189 B) and its neighbours."""
import json, idaapi, idc, idautils, ida_funcs, ida_bytes, ida_ua
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\rebase_probe3.json"
R = {"heads": [], "fresh": []}
for h in idautils.Heads(0x6DEF0, 0x6DFF0):
    f = ida_funcs.get_func(h)
    R["heads"].append([h, ida_bytes.get_item_size(h), "C" if ida_bytes.is_code(ida_bytes.get_flags(h)) else "D",
                       idc.get_func_name(h) if f else "", idc.generate_disasm_line(h, 0)])
x = 0x6DF27
while x < 0x6DF27 + 189:
    insn = ida_ua.insn_t()
    n = ida_ua.decode_insn(insn, x)
    R["fresh"].append([x, n, idc.print_insn_mnem(x) if n > 0 else None])
    x += n if n > 0 else 1
R["func_6DE83"] = [ida_funcs.get_func(0x6DF25).start_ea, ida_funcs.get_func(0x6DF25).end_ea]
open(OUT, "w").write(json.dumps(R))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
