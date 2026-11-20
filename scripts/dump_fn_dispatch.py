import idc
import idaapi
import ida_funcs
from pathlib import Path

out_lines = []
for name, ea in [("fn_table_dispatch", idc.get_name_ea_simple("fn_table_dispatch")), ("far_cb_4", idc.get_name_ea_simple("far_cb_4")), ("sub_112373", 0x112373)]:
    if ea != idc.BADADDR:
        fn = ida_funcs.get_func(ea)
        out_lines.append(f"FUNCTION {name} at 0x{ea:x}:")
        cur = fn.start_ea if fn else ea
        end = fn.end_ea if fn else ea + 64
        while cur < end:
            dis = idc.generate_disasm_line(cur, 0)
            out_lines.append(f"  0x{cur:06x}: {dis}")
            cur = idc.next_head(cur, end)

out_file = Path("analysis/fn_dispatch_disasm.txt")
with open(out_file, "w") as f:
    f.write("\n".join(out_lines))

idc.qexit(0)
