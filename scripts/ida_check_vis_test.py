import idaapi
import idc

idaapi.auto_wait()

ea = 0x28A98
target = idc.get_operand_value(ea, 0)
print(f"Call at 0x{ea:X} target: 0x{target:X} ({idc.get_name(target)})")

func = idaapi.get_func(target)
if func:
    cur = func.start_ea
    while cur < min(func.start_ea + 100, func.end_ea):
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ""
        print(f"  0x{cur:08X}: {dis}  ; {cmt}")
        cur = idc.next_head(cur, func.end_ea)

with open(r'c:\Users\yotam\projects\falcon3\temp\vis_test_target.txt', 'w') as f:
    f.write(f"target: 0x{target:X}\n")

idc.qexit(0)
