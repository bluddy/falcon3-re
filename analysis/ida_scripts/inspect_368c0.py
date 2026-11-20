import idaapi
import idc
import idautils

idaapi.auto_wait()

ea = 0x10000 + 0x26AC0 - 0x200
with open("analysis/ida_scripts/inspect_368c0.txt", "w") as f:
    f.write(f"Address 0x{ea:X}: {idaapi.get_bytes(ea, 32)}\n")
    for xref in idautils.XrefsTo(ea):
        f.write(f"  Xref from 0x{xref.frm:X}\n")

idc.qexit(0)
