import idaapi
import idc

idaapi.auto_wait()

func = idaapi.get_func(0x26C4A)
with open("analysis/ida_scripts/entity_draw_handler.txt", "w") as f:
    if func:
        f.write(f"Function from 0x{func.start_ea:X} to 0x{func.end_ea:X}\n")
        cur = func.start_ea
        while cur < func.end_ea:
            dis = idc.generate_disasm_line(cur, 0)
            cmt = idc.get_cmt(cur, 0) or ''
            f.write(f"0x{cur:08X}: {dis:45s} ; {cmt}\n")
            cur = idc.next_head(cur, func.end_ea)

idc.qexit(0)
