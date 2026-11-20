import idc
import ida_funcs
from pathlib import Path

idc.auto_wait()
ea = 0x2EBE5
fn = ida_funcs.get_func(ea)
lines = []
if fn:
    lines.append(f"Function at 0x{fn.start_ea:x}..0x{fn.end_ea:x}")
    cur = fn.start_ea
    while cur < fn.end_ea:
        dis = idc.generate_disasm_line(cur, 0)
        lines.append(f"  0x{cur:08x}: {dis}")
        cur = idc.next_head(cur, fn.end_ea)

Path('analysis/objects_loader_full.txt').write_text('\n'.join(lines))
idc.qexit(0)
