
import idaapi, idc

idaapi.auto_wait()

with open('poly_vis_detail.txt', 'w') as f:
    ea = 0x297FD
    for _ in range(60):
        dis = idc.generate_disasm_line(ea, 0)
        cmt = idc.get_cmt(ea, 0) or ''
        f.write(f'0x{ea:08X}: {dis:40s} ; {cmt}\n')
        ea = idc.next_head(ea, 0x29917)
        if ea >= 0x29917: break

idc.qexit(0)
