import idc
import idaapi

idaapi.auto_wait()

out_lines = []
for cur in range(0x26B50, 0x26B80):
    dis = idc.generate_disasm_line(cur, 0)
    if dis:
        out_lines.append(f"0x{cur:08X}: {dis}")

with open(r'analysis/viewer/disasm_26b50_26b80.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
