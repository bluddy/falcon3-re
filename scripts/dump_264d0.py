import idc
import idaapi

idaapi.auto_wait()

out_lines = []
cur = 0x264D0
end = 0x26520
while cur < end:
    dis = idc.generate_disasm_line(cur, 0)
    cmt = idc.get_cmt(cur, 0) or ""
    out_lines.append(f"0x{cur:08X}: {dis}  ; {cmt}")
    cur = idc.next_head(cur, end)

with open(r'analysis/viewer/disasm_264d0.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
