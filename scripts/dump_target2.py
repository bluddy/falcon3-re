import idc
import idaapi

idaapi.auto_wait()

out_lines = []
cur = 0x24913
for _ in range(30):
    dis = idc.generate_disasm_line(cur, 0)
    out_lines.append(f"0x{cur:08X}: {dis}")
    cur = idc.next_head(cur)

with open(r'analysis/viewer/disasm_target_24913.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
