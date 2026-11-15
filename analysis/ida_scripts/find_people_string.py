"""
Find where "PEOPLE" string is referenced
"""
import idaapi
import idautils
import idc

# Search for PEOPLE string
for s in idautils.Strings():
    if 'PEOPLE' in str(s).upper():
        print(f"\nFound string at 0x{s.ea:X}: \"{s}\"")
        
        # Find all xrefs to this string
        for xref in idautils.XrefsTo(s.ea, 0):
            func_name = idc.get_func_name(xref.frm)
            print(f"  Referenced from 0x{xref.frm:X} in {func_name}")
            print(f"    {idc.generate_disasm_line(xref.frm, 0)}")

idc.qexit(0)
