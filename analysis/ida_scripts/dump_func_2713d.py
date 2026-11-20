import idaapi
import idc

idaapi.auto_wait()

func = idaapi.get_func(0x2713D)
with open("analysis/ida_scripts/func_2713d_full.txt", "w") as f:
    if func:
        f.write(f"Function from 0x{func.start_ea:X} to 0x{func.end_ea:X}\n")
        cur = func.start_ea
        while cur < func.end_ea:
            dis = idc.generate_disasm_line(cur, 0)
            cmt = idc.get_cmt(cur, 0) or ''
            f.write(f"0x{cur:08X}: {dis:45s} ; {cmt}\n")
            cur = idc.next_head(cur, func.end_ea)
    else:
        f.write("Function not found, dumping raw from 0x270B0 to 0x271A0:\n")
        cur = 0x270B0
        while cur < 0x271A0:
            dis = idc.generate_disasm_line(cur, 0)
            cmt = idc.get_cmt(cur, 0) or ''
            f.write(f"0x{cur:08X}: {dis:45s} ; {cmt}\n")
            cur = idc.next_head(cur, 0x271A0)

idc.qexit(0)
