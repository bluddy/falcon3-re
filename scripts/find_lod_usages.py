import idc
import idaapi
import idautils

idaapi.auto_wait()

out_lines = []

# Search for references to word_1F716 (which holds si = LOD table pointer)
ea = idc.get_name_ea_simple("word_1F716")
out_lines.append(f"References to word_1F716 (0x{ea:X}):")
for ref in idautils.DataRefsTo(ea):
    func = idaapi.get_func(ref)
    fname = idc.get_name(func.start_ea) if func else "no_func"
    dis = idc.generate_disasm_line(ref, 0)
    out_lines.append(f"  0x{ref:08X} in {fname}: {dis}")

with open(r'analysis/viewer/refs_to_word_1f716.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
