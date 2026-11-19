import idaapi
import idc

idaapi.auto_wait()

out_lines = []
funcs_to_dump = [0x14B4F, 0x14EAE, 0x142DA, 0x28874, 0x28E50, 0x29917, 0x2061B, 0x2063B]

for ea in funcs_to_dump:
    func = idaapi.get_func(ea)
    if func:
        out_lines.append(f"\n{'='*70}\nFunction {idc.get_name(ea)} at 0x{ea:X} - 0x{func.end_ea:X}:\n{'='*70}")
        cur = func.start_ea
        while cur < func.end_ea:
            dis = idc.generate_disasm_line(cur, 0)
            cmt = idc.get_cmt(cur, 0) or ""
            out_lines.append(f"  0x{cur:08X}: {dis}  ; {cmt}")
            cur = idc.next_head(cur, func.end_ea)

with open(r'c:\Users\yotam\projects\falcon3\temp\isldat_render_flow_disasm.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
