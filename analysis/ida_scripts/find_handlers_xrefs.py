import idaapi
import idc
import idautils

idaapi.auto_wait()

# Search for references to the 72 object descriptors or entity table
# Let's search for "farobj_entity_type_handlers" xrefs:
handlers_ea = 0x26426
with open("analysis/ida_scripts/handlers_xrefs.txt", "w") as f:
    f.write(f"Xrefs to handlers table at 0x{handlers_ea:X}:\n")
    for xref in idautils.XrefsTo(handlers_ea):
        f.write(f"  Xref from 0x{xref.frm:X}\n")
        func = idaapi.get_func(xref.frm)
        if func:
            f.write(f"    In func 0x{func.start_ea:X} - 0x{func.end_ea:X} ({idc.get_func_name(func.start_ea)})\n")

idc.qexit(0)
