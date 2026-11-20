import idaapi
import idc

idaapi.auto_wait()

ea = idaapi.get_fileregion_ea(0x26AC0)
with open("analysis/ida_scripts/objects_addr.txt", "w") as f:
    f.write(f"File offset 0x26AC0 -> EA 0x{ea:X}\n")
    if ea != idc.BADADDR:
        f.write(f"Disasm at EA: {idc.generate_disasm_line(ea, 0)}\n")
        import idautils
        for xref in idautils.XrefsTo(ea):
            f.write(f"  Xref from 0x{xref.frm:X}\n")

idc.qexit(0)
