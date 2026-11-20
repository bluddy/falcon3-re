import idc
import idaapi
import idautils

idaapi.auto_wait()

out_lines = []

addrs = [0x26B2E, 0x28CA1, 0x28CA2, 0x2978E, 0x299D5]

for ea in addrs:
    func = idaapi.get_func(ea)
    if func:
        name = idc.get_name(ea)
        out_lines.append(f"\n{'='*70}\nFunction {name} at 0x{func.start_ea:X} - 0x{func.end_ea:X}:\n{'='*70}")
        cur = func.start_ea
        while cur < func.end_ea:
            dis = idc.generate_disasm_line(cur, 0)
            cmt = idc.get_cmt(cur, 0) or ""
            rpt_cmt = idc.get_cmt(cur, 1) or ""
            full_cmt = f"; {cmt} {rpt_cmt}".strip()
            out_lines.append(f"  0x{cur:08X}: {dis}  {full_cmt}")
            cur = idc.next_head(cur, func.end_ea)
    else:
        out_lines.append(f"No func at 0x{ea:X}")

with open(r'analysis/viewer/disasm_3d_pipeline.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
