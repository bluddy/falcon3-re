import idc
import idaapi
import idautils
import ida_bytes
import ida_funcs
from pathlib import Path

idaapi.auto_wait()

out_lines = []
out_lines.append("=== Searching for REPORT.DAT references ===")

# Search for REPORT.DAT string
pattern = b"REPORT.DAT"
ea = ida_bytes.bin_search(0, ida_bytes.BADADDR, pattern, None, ida_bytes.BIN_SEARCH_FORWARD, ida_bytes.BIN_SEARCH_CASE)
while ea != ida_bytes.BADADDR:
    out_lines.append(f"Found REPORT.DAT at 0x{ea:08x}")
    for xref in idautils.XrefsTo(ea):
        frm = xref.frm
        fn_name = ida_funcs.get_func_name(frm)
        out_lines.append(f"  xref from 0x{frm:08x} in function {fn_name}")
    ea = ida_bytes.bin_search(ea + len(pattern), ida_bytes.BADADDR, pattern, None, ida_bytes.BIN_SEARCH_FORWARD, ida_bytes.BIN_SEARCH_CASE)

out_path = Path("analysis/report_ida_results.txt")
with open(out_path, "w") as f:
    f.write("\n".join(out_lines))

idc.qexit(0)
