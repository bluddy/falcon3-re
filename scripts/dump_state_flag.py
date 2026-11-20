import idc
import idaapi

idaapi.auto_wait()

ea = idc.get_name_ea_simple("state_flag_unpack_1f735")
out_lines = [f"Function {idc.get_name(ea)} at 0x{ea:X}:"]
func = idaapi.get_func(ea)
if func:
    cur = func.start_ea
    while cur < func.end_ea:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ""
        out_lines.append(f"  0x{cur:08X}: {dis}  ; {cmt}")
        cur = idc.next_head(cur, func.end_ea)

with open(r'analysis/viewer/disasm_state_flag_unpack.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
