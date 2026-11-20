import idc
import idaapi
import ida_funcs
from pathlib import Path

# Find where dispatch_22178_then_27474_0 goes
addr = idc.get_name_ea_simple("dispatch_22178_then_27474_0")
out_lines = []
if addr != idc.BADADDR:
    fn = ida_funcs.get_func(addr)
    out_lines.append(f"FUNCTION dispatch_22178_then_27474_0 at 0x{addr:x}:")
    cur = fn.start_ea
    while cur < fn.end_ea:
        dis = idc.generate_disasm_line(cur, 0)
        out_lines.append(f"  0x{cur:06x}: {dis}")
        cur = idc.next_head(cur, fn.end_ea)

out_file = Path("analysis/dispatch_22178_disasm.txt")
with open(out_file, "w") as f:
    f.write("\n".join(out_lines))

idc.qexit(0)
