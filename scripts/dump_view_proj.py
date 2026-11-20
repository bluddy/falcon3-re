import idc
import idaapi
import ida_funcs
from pathlib import Path

ea = idc.get_name_ea_simple("view_projection")
out_lines = []
if ea != idc.BADADDR:
    fn = ida_funcs.get_func(ea)
    out_lines.append(f"FUNCTION view_projection at 0x{ea:x}..0x{fn.end_ea:x}:")
    cur = fn.start_ea
    while cur < fn.end_ea:
        dis = idc.generate_disasm_line(cur, 0)
        out_lines.append(f"  0x{cur:06x}: {dis}")
        cur = idc.next_head(cur, fn.end_ea)

out_file = Path("analysis/view_projection_disasm.txt")
with open(out_file, "w") as f:
    f.write("\n".join(out_lines))

idc.qexit(0)
