import idc
import idaapi
import ida_funcs
from pathlib import Path

funcs_to_dump = [0x1121E9, 0x112090, 0x11230C, 0x1123AD]
out_lines = []

for ea in funcs_to_dump:
    fn = ida_funcs.get_func(ea)
    if not fn: continue
    fn_name = ida_funcs.get_func_name(ea)
    out_lines.append(f"\n{'='*80}\nFUNCTION: {fn_name} at 0x{ea:x} (size {fn.end_ea - fn.start_ea})\n{'='*80}")
    cur = fn.start_ea
    while cur < fn.end_ea:
        dis = idc.generate_disasm_line(cur, 0)
        out_lines.append(f"  0x{cur:06x}: {dis}")
        cur = idc.next_head(cur, fn.end_ea)

out_file = Path("analysis/report_draw_disasm.txt")
with open(out_file, "w") as f:
    f.write("\n".join(out_lines))

idc.qexit(0)
