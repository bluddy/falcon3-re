import idc
import idaapi
import idautils

idaapi.auto_wait()

ea = 0x2978E
out_lines = [f"Xrefs to 0x{ea:X} ({idc.get_name(ea)}):"]
for ref in idautils.CodeRefsTo(ea, 0):
    func = idaapi.get_func(ref)
    fname = idc.get_name(func.start_ea) if func else "no_func"
    dis = idc.generate_disasm_line(ref, 0)
    out_lines.append(f"  Code ref: 0x{ref:08X} in {fname}: {dis}")

for ref in idautils.DataRefsTo(ea):
    func = idaapi.get_func(ref)
    fname = idc.get_name(func.start_ea) if func else "no_func"
    dis = idc.generate_disasm_line(ref, 0)
    out_lines.append(f"  Data ref: 0x{ref:08X} in {fname}: {dis}")

with open(r'analysis/viewer/xrefs_to_2978e.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
