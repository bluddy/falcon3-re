"""
Find the .RFM file loader by tracing xrefs.
FIXED: Using correct string address from previous analysis.
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\rfm_loader_fixed.txt"

with open(output_file, 'w') as f:
    f.write("=== FIXED RFM LOADER SEARCH ===\n\n")
    
    # From rfm_string_area.txt, we know the string is at 0x151381
    rfm_string_addr = 0x151381
    
    f.write(f"String address: 0x{rfm_string_addr:X}\n")
    
    # Verify the string exists
    string_val = idc.get_strlit_contents(rfm_string_addr)
    if string_val:
        f.write(f"String value: {string_val}\n\n")
    else:
        f.write("ERROR: String not found at this address!\n\n")
    
    # Get xrefs
    f.write("Cross-references:\n")
    f.write("=" * 80 + "\n\n")
    
    xref_count = 0
    for xref in idautils.XrefsTo(rfm_string_addr):
        xref_count += 1
        f.write(f"XREF #{xref_count}:\n")
        f.write(f"  From: 0x{xref.frm:X}\n")
        f.write(f"  Type: {xref.type}\n")
        
        func = idaapi.get_func(xref.frm)
        if func:
            func_name = idc.get_func_name(xref.frm)
            f.write(f"  Function: {func_name} @ 0x{func.start_ea:X}\n")
            f.write(f"  Size: {func.end_ea - func.start_ea} bytes\n\n")
            
            # Context
            f.write("  Context:\n")
            for i in range(-10, 11):
                addr = xref.frm + (i * 4)
                if addr >= func.start_ea and addr < func.end_ea:
                    disasm = idc.generate_disasm_line(addr, 0)
                    marker = " >>> " if i == 0 else "     "
                    f.write(f"{marker}0x{addr:X}: {disasm}\n")
        else:
            f.write(f"  Not in a function\n")
        
        f.write("\n")
    
    if xref_count == 0:
        f.write("NO XREFS FOUND!\n")
        f.write("This confirms the string is not directly referenced.\n")
        f.write("The filename must be built dynamically at runtime.\n\n")
        
        # Try searching nearby
        f.write("=" * 80 + "\n")
        f.write("SEARCHING NEARBY ADDRESSES FOR XREFS:\n")
        f.write("=" * 80 + "\n\n")
        
        for offset in range(-20, 21, 2):
            test_addr = rfm_string_addr + offset
            test_xrefs = list(idautils.XrefsTo(test_addr))
            if test_xrefs:
                f.write(f"\nFound {len(test_xrefs)} xrefs at offset {offset:+d} (0x{test_addr:X}):\n")
                for xref in test_xrefs[:3]:  # Show first 3
                    func = idaapi.get_func(xref.frm)
                    if func:
                        func_name = idc.get_func_name(xref.frm)
                        f.write(f"  - 0x{xref.frm:X} in {func_name}\n")
    else:
        f.write(f"\nTotal xrefs: {xref_count}\n")

print(f"Analysis complete: {output_file}")
idc.qexit(0)
