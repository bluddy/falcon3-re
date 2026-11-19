import idaapi
import idc
import idautils

idaapi.auto_wait()

out_lines = []
# Find isldat_swap_flag
name = "isldat_swap_flag"
ea = idc.get_name_ea_simple(name)
out_lines.append(f"Address of {name}: 0x{ea:X}")

if ea != idc.BADADDR:
    xrefs = list(idautils.XrefsTo(ea, 0))
    out_lines.append(f"Xrefs to {name} ({len(xrefs)}):")
    for xr in xrefs:
        func = idaapi.get_func(xr.frm)
        fname = idc.get_name(func.start_ea) if func else "none"
        dis = idc.generate_disasm_line(xr.frm, 0)
        out_lines.append(f"  0x{xr.frm:08X} in {fname}: {dis}")

with open(r'c:\Users\yotam\projects\falcon3\temp\swap_flag_xrefs.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
