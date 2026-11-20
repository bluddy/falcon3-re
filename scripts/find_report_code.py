import idc
import idaapi
import idautils
import ida_segment
import ida_funcs
import json
from pathlib import Path

str_ea = 0x1115b9
seg = ida_segment.getseg(str_ea)
seg_name = ida_segment.get_segm_name(seg) if seg else "none"
seg_start = seg.start_ea if seg else 0
off = str_ea - seg_start

print(f"REPORT.DAT at 0x{str_ea:x} in segment '{seg_name}' (start 0x{seg_start:x}), offset within seg = 0x{off:04x}")

# Search for instructions with immediate value 'off' (0x{off:04x})
matches = []
for segea in idautils.Segments():
    s = ida_segment.getseg(segea)
    sname = ida_segment.get_segm_name(s)
    # Search code segments
    if s.type == ida_segment.SEG_CODE:
        for head in idautils.Heads(s.start_ea, s.end_ea):
            for op_idx in range(2):
                if idc.get_operand_value(head, op_idx) == off:
                    fn = ida_funcs.get_func(head)
                    fn_name = ida_funcs.get_func_name(head) if fn else "none"
                    matches.append({
                        "ea": hex(head),
                        "seg": sname,
                        "disasm": idc.generate_disasm_line(head, 0),
                        "func": fn_name
                    })

out_file = Path("analysis/report_dat_code_xrefs.json")
with open(out_file, "w") as f:
    json.dump({
        "str_ea": hex(str_ea),
        "seg_name": seg_name,
        "seg_start": hex(seg_start),
        "offset": hex(off),
        "matches": matches
    }, f, indent=2)

print(f"Found {len(matches)} matches! Saved to {out_file}")
idc.qexit(0)
