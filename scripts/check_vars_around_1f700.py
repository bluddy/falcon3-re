import idc
import idaapi

idaapi.auto_wait()

out_lines = []
for ea in range(0x1F700, 0x1F750):
    name = idc.get_name(ea)
    cmt = idc.get_cmt(ea, 0) or ""
    val = idc.get_wide_byte(ea)
    wval = idc.get_wide_word(ea)
    if name:
        out_lines.append(f"0x{ea:X} ({name}): byte=0x{val:02X}, word=0x{wval:04X}  ; {cmt}")

with open(r'analysis/viewer/vars_around_1f700.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
