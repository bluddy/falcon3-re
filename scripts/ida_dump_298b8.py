import idaapi
import idc

idaapi.auto_wait()

ea = 0x298B8
lines = []
cur = ea
while cur < 0x29920:
    dis = idc.generate_disasm_line(cur, 0)
    cmt = idc.get_cmt(cur, 0) or ""
    lines.append(f"  0x{cur:08X}: {dis}  ; {cmt}")
    cur = idc.next_head(cur)

with open(r'c:\Users\yotam\projects\falcon3\temp\func_298b8_dump.txt', 'w') as f:
    f.write('\n'.join(lines))

idc.qexit(0)
