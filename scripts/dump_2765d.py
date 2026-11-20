import idc
import idaapi
import ida_funcs
from pathlib import Path

fn = ida_funcs.get_func(0x2765D)
out_lines = []
if fn:
    fn_name = ida_funcs.get_func_name(0x2765D)
    out_lines.append(f"FUNCTION: {fn_name} at 0x2765D (size {fn.end_ea - fn.start_ea})")
    cur = fn.start_ea
    while cur < fn.end_ea:
        dis = idc.generate_disasm_line(cur, 0)
        out_lines.append(f"  0x{cur:06x}: {dis}")
        cur = idc.next_head(cur, fn.end_ea)

out_file = Path("analysis/sub_2765d_disasm.txt")
with open(out_file, "w") as f:
    f.write("\n".join(out_lines))

idc.qexit(0)
