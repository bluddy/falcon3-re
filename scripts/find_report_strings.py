import idc
import idautils
import ida_funcs
import json
from pathlib import Path

results = []
strings = idautils.Strings()
for s in strings:
    str_val = str(s)
    if "REPORT.DAT" in str_val or "VGRAPH" in str_val or "OBJECTS" in str_val:
        xrefs = []
        for xref in idautils.XrefsTo(s.ea):
            fn = ida_funcs.get_func(xref.frm)
            fn_name = ida_funcs.get_func_name(xref.frm) if fn else "none"
            xrefs.append({"frm": hex(xref.frm), "func": fn_name})
        results.append({
            "ea": hex(s.ea),
            "string": str_val,
            "length": s.length,
            "xrefs": xrefs
        })

out_file = Path("analysis/report_dat_ida_xrefs.json")
with open(out_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"Found {len(results)} matches! Saved to {out_file}")
idc.qexit(0)
