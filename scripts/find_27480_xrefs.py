import idc
import idaapi
import ida_funcs
import idautils
from pathlib import Path

target_ea = 0x27480
out_lines = []
out_lines.append(f"Xrefs to word_27480 (0x{target_ea:x}):")

for xref in idautils.XrefsTo(target_ea):
    frm = xref.frm
    fn = ida_funcs.get_func(frm)
    fn_name = ida_funcs.get_func_name(frm) if fn else "none"
    dis = idc.generate_disasm_line(frm, 0)
    out_lines.append(f"  from 0x{frm:06x} in {fn_name}: {dis}")

# Also check functions that read cs:word_27480
seg = idaapi.getseg(target_ea)
for head in idautils.Heads(seg.start_ea, seg.end_ea):
    dis = idc.generate_disasm_line(head, 0)
    if "27480" in dis or "27482" in dis:
        fn = ida_funcs.get_func(head)
        fn_name = ida_funcs.get_func_name(head) if fn else "none"
        out_lines.append(f"  at 0x{head:06x} in {fn_name}: {dis}")

out_file = Path("analysis/word_27480_xrefs.txt")
with open(out_file, "w") as f:
    f.write("\n".join(out_lines))

idc.qexit(0)
