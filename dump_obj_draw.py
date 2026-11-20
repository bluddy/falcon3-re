
import idaapi, idc, idautils

idaapi.auto_wait()

with open('object_draw_full.txt', 'w') as f:
    ea = 0x26B2E
    func = idaapi.get_func(ea)
    if func:
        f.write(f'=== Function {idc.get_name(func.start_ea)} at 0x{func.start_ea:X} - 0x{func.end_ea:X} ===\n')
        cur = func.start_ea
        while cur < func.end_ea:
            dis = idc.generate_disasm_line(cur, 0)
            cmt = idc.get_cmt(cur, 0) or ''
            f.write(f'  0x{cur:08X}: {dis:40s} ; {cmt}\n')
            cur = idc.next_head(cur, func.end_ea)

idc.qexit(0)
