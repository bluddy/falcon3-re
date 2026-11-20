import idc
import idaapi
import ida_funcs
from pathlib import Path

# Dump disassembly of functions around 0x111AF6
funcs_to_dump = [0x111AF6, 0x111F0C, 0x1120D1]
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

out_file = Path("analysis/report_loader_disasm.txt")
with open(out_file, "w") as f:
    f.write("\n".join(out_lines))

idc.qexit(0)
