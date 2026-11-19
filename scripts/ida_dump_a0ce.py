import idaapi
import idc

idaapi.auto_wait()

ea = 0xA0CE
func = idaapi.get_func(ea)
lines = []
if func:
    lines.append(f"Function {idc.get_name(func.start_ea)} at 0x{func.start_ea:X} - 0x{func.end_ea:X}:")
    cur = func.start_ea
    while cur < func.end_ea:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ""
        lines.append(f"  0x{cur:08X}: {dis}  ; {cmt}")
        cur = idc.next_head(cur, func.end_ea)
else:
    # Maybe near or chunk?
    lines.append(f"No func at 0x{ea:X}, dumping 100 bytes:")
    cur = ea
    for _ in range(30):
        dis = idc.generate_disasm_line(cur, 0)
        lines.append(f"  0x{cur:08X}: {dis}")
        cur = idc.next_head(cur)

with open(r'c:\Users\yotam\projects\falcon3\temp\func_a0ce_dump.txt', 'w') as f:
    f.write('\n'.join(lines))

idc.qexit(0)
