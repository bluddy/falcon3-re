import idaapi
import idc

idaapi.auto_wait()

ea = 0x2978E
func = idaapi.get_func(ea)
lines = []
if func:
    lines.append(f"Function {idc.get_name(func.start_ea)} at 0x{func.start_ea:X} - 0x{func.end_ea:X}:")
    cur = func.start_ea
    while cur < min(func.start_ea + 300, func.end_ea):
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ""
        lines.append(f"  0x{cur:08X}: {dis}  ; {cmt}")
        cur = idc.next_head(cur, func.end_ea)

with open(r'c:\Users\yotam\projects\falcon3\temp\func_2978e_dump.txt', 'w') as f:
    f.write('\n'.join(lines))

idc.qexit(0)
