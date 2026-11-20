import idaapi
import idc
import idautils

idaapi.auto_wait()

target = 0x26B2E
with open("analysis/ida_scripts/xrefs_draw.txt", "w") as f:
    f.write(f"Xrefs to 0x{target:X}:\n")
    for xref in idautils.XrefsTo(target):
        f.write(f"  From 0x{xref.frm:X} (type {xref.type})\n")

idc.qexit(0)
