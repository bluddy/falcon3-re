"""
Examine the area around the *.RFM string at 0x151381
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\rfm_string_area.txt"

with open(output_file, 'w') as f:
    f.write("=== RFM String Area Analysis ===\n\n")
    
    rfm_str_addr = 0x151381
    
    f.write(f"String address: 0x{rfm_str_addr:X}\n")
    
    # Get the string
    str_val = idc.get_strlit_contents(rfm_str_addr)
    f.write(f"String value: {str_val}\n\n")
    
    # Check nearby strings (within ±100 bytes)
    f.write("=" * 80 + "\n")
    f.write("NEARBY STRINGS (±100 bytes):\n")
    f.write("=" * 80 + "\n\n")
    
    for offset in range(-100, 101):
        addr = rfm_str_addr + offset
        test_str = idc.get_strlit_contents(addr)
        if test_str and len(test_str) > 3:
            f.write(f"0x{addr:X} (+{offset}): {test_str}\n")
    
    # Check if this is part of a string table
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("STRING TABLE ANALYSIS:\n")
    f.write("=" * 80 + "\n\n")
    
    # Look backward to find the start of a potential table
    search_start = rfm_str_addr - 500
    search_end = rfm_str_addr + 500
    
    f.write(f"Scanning range: 0x{search_start:X} to 0x{search_end:X}\n\n")
    
    strings_found = []
    for string_addr in idautils.Strings():
        if search_start <= string_addr.ea <= search_end:
            strings_found.append((string_addr.ea, str(string_addr)))
    
    strings_found.sort()
    for addr, s in strings_found:
        offset_from_rfm = addr - rfm_str_addr
        f.write(f"0x{addr:X} ({offset_from_rfm:+d}): {s}\n")
    
    # Check for xrefs to the general area (not just the specific string)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("XREFS TO NEARBY ADDRESSES:\n")
    f.write("=" * 80 + "\n\n")
    
    # Check each address in a range
    for offset in range(-50, 51, 2):
        addr = rfm_str_addr + offset
        xref_count = 0
        for xref in idautils.XrefsTo(addr):
            xref_count += 1
            if xref_count == 1:
                f.write(f"\n0x{addr:X} ({offset:+d}):\n")
            
            func = idaapi.get_func(xref.frm)
            if func:
                func_name = idc.get_func_name(xref.frm)
                f.write(f"  From: 0x{xref.frm:X} in {func_name}\n")
                
                # Show context
                for i in range(-2, 3):
                    ctx_addr = xref.frm + (i * 4)
                    if ctx_addr >= func.start_ea and ctx_addr < func.end_ea:
                        disasm = idc.generate_disasm_line(ctx_addr, 0)
                        if disasm:
                            marker = " >>>" if i == 0 else "    "
                            f.write(f"  {marker} 0x{ctx_addr:X}: {disasm}\n")

print(f"Analysis complete: {output_file}")
idc.qexit(0)
