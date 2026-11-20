import idc
import idaapi

idaapi.auto_wait()

out_lines = []
funcs = [0x26CDF, 0x2814E, 0x286D5]

for ea in funcs:
    func = idaapi.get_func(ea)
    if func:
        fname = idc.get_name(ea)
        out_lines.append(f"\n{'='*70}\nFunction {fname} at 0x{func.start_ea:X} - 0x{func.end_ea:X}:\n{'='*70}")
        cur = func.start_ea
        while cur < func.end_ea:
            dis = idc.generate_disasm_line(cur, 0)
            cmt = idc.get_cmt(cur, 0) or ""
            out_lines.append(f"  0x{cur:08X}: {dis}  ; {cmt}")
            cur = idc.next_head(cur, func.end_ea)

with open(r'analysis/viewer/disasm_other_3d_funcs.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
