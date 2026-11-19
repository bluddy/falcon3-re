import idaapi
import idc
import idautils

idaapi.auto_wait()

ea = 0x12FC4 # isldat_state_load
xrefs = list(idautils.XrefsTo(ea, 0))
lines = [f"Xrefs to isldat_state_load (0x{ea:X}): {len(xrefs)}"]

for xr in xrefs:
    func = idaapi.get_func(xr.frm)
    fname = idc.get_name(func.start_ea) if func else "none"
    dis = idc.generate_disasm_line(xr.frm, 0)
    lines.append(f"  0x{xr.frm:08X} in {fname}: {dis}")

with open(r'c:\Users\yotam\projects\falcon3\temp\isldat_load_xrefs.txt', 'w') as f:
    f.write('\n'.join(lines))

idc.qexit(0)
