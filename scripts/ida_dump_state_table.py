import idaapi
import idc

idaapi.auto_wait()

out_lines = []
func = idaapi.get_func(0x13079)
if func:
    out_lines.append(f"Function {idc.get_name(func.start_ea)} at 0x{func.start_ea:X} - 0x{func.end_ea:X}:")
    cur = func.start_ea
    while cur < func.end_ea:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ""
        out_lines.append(f"  0x{cur:08X}: {dis}  ; {cmt}")
        cur = idc.next_head(cur, func.end_ea)

with open(r'c:\Users\yotam\projects\falcon3\temp\state_table_apply_dump.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
