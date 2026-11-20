
import idaapi, idc

idaapi.auto_wait()

with open('poly_render_funcs.txt', 'w') as f:
    seg_base = 0x1F6C0 # seg020
    for off in [0xA0CE, 0x9790]:
        ea = seg_base + off
        f.write(f'=== Address 0x{ea:X} (seg020:0x{off:04X}) ===\n')
        cur = ea
        for _ in range(50):
            dis = idc.generate_disasm_line(cur, 0)
            cmt = idc.get_cmt(cur, 0) or ''
            f.write(f'  0x{cur:08X}: {dis:40s} ; {cmt}\n')
            cur = idc.next_head(cur, ea + 400)
            if 'ret' in dis: break

idc.qexit(0)
