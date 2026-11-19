import idaapi
import idc

idaapi.auto_wait()

out_lines = []
ea = 0x28B08
func = idaapi.get_func(ea)
if func:
    out_lines.append(f"\nFunction {idc.get_name(ea)} at 0x{ea:X} - 0x{func.end_ea:X}:")
    cur = func.start_ea
    while cur < func.end_ea:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ""
        out_lines.append(f"  0x{cur:08X}: {dis}  ; {cmt}")
        cur = idc.next_head(cur, func.end_ea)

with open(r'c:\Users\yotam\projects\falcon3\temp\line_draw_dump.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
