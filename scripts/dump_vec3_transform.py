import idc
import idaapi

idaapi.auto_wait()

ea = idc.get_name_ea_simple("fixed_vec3_transform_es")
if ea == idc.BADADDR:
    ea = 0x22C5C # let's check the target of call at 0x26B64
# let's find call target at 0x26B64
target = idc.get_operand_value(0x26B64, 0)
print(f"Target of 0x26B64: 0x{target:X}")

func = idaapi.get_func(target)
out_lines = []
if func:
    cur = func.start_ea
    while cur < func.end_ea:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ""
        out_lines.append(f"  0x{cur:08X}: {dis}  ; {cmt}")
        cur = idc.next_head(cur, func.end_ea)

with open(r'analysis/viewer/disasm_fixed_vec3_transform.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
