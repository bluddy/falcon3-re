import idc
import idaapi
import ida_funcs
import idautils
from pathlib import Path

out_lines = []
for ea in [0x0275d8, 0x02760a]:
    out_lines.append(f"Xrefs to 0x{ea:x}:")
    for xref in idautils.XrefsTo(ea):
        frm = xref.frm
        fn = ida_funcs.get_func(frm)
        fn_name = ida_funcs.get_func_name(frm) if fn else "none"
        dis = idc.generate_disasm_line(frm, 0)
        out_lines.append(f"  from 0x{frm:06x} in {fn_name}: {dis}")

out_file = Path("analysis/stream_reader_xrefs.txt")
with open(out_file, "w") as f:
    f.write("\n".join(out_lines))

idc.qexit(0)
