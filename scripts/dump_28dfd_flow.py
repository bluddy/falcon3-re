import idc
import idaapi

idaapi.auto_wait()

out_lines = []
cur = 0x28DFD
end = 0x28E50

while cur < end:
    dis = idc.generate_disasm_line(cur, 0)
    cmt = idc.get_cmt(cur, 0) or ""
    rpt_cmt = idc.get_cmt(cur, 1) or ""
    full_cmt = f"; {cmt} {rpt_cmt}".strip()
    name = idc.get_name(cur)
    lbl = f"{name}:" if name else ""
    out_lines.append(f"{lbl:20s} 0x{cur:08X}: {dis}  {full_cmt}")
    nxt = idc.next_head(cur, end)
    if nxt <= cur:
        cur += 1
    else:
        cur = nxt

with open(r'analysis/viewer/disasm_28dfd.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
