
import idaapi, idc

idaapi.auto_wait()

with open('func_28ca2.txt', 'w') as f:
    ea = 0x28D8D
    for _ in range(40):
        dis = idc.generate_disasm_line(ea, 0)
        cmt = idc.get_cmt(ea, 0) or ''
        f.write(f'0x{ea:08X}: {dis:40s} ; {cmt}\n')
        ea = idc.next_head(ea, 0x28E30)

idc.qexit(0)
