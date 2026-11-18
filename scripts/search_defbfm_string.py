"""
Search for "DEFBFM" string in the binary
"""

import idc
import idaapi
import idautils

idaapi.auto_wait()

output_file = r"C:\Users\ybarnoy\projects\falcon3\temp\defbfm_search.txt"

with open(output_file, 'w') as f:
    f.write("=== DEFBFM String Search ===\n\n")
    
    # Search for the string "DEFBFM"
    search_str = b"DEFBFM"
    
    f.write(f"Searching for: {search_str}\n\n")
    
    # Get all segments
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        f.write(f"Searching segment: {seg_name} (0x{seg_start:X} - 0x{seg_end:X})\n")
        
        # Search in this segment
        addr = seg_start
        while addr < seg_end:
            found_addr = idc.find_binary(addr, seg_end, "44 45 46 42 46 4D", 16, idc.SEARCH_DOWN)
            if found_addr == idaapi.BADADDR:
                break
            
            f.write(f"\nFound at 0x{found_addr:X}\n")
            
            # Get context (16 bytes before and after)
            f.write("Context:\n")
            for i in range(-16, 17):
                b = idc.get_wide_byte(found_addr + i)
                if b is not None:
                    marker = " >>>" if i == 0 else "    "
                    char = chr(b) if 32 <= b < 127 else '.'
                    f.write(f"{marker} 0x{found_addr + i:X}: 0x{b:02X} ('{char}')\n")
            
            # Check for xrefs
            f.write("\nXrefs to this location:\n")
            xref_count = 0
            for xref in idautils.XrefsTo(found_addr):
                xref_count += 1
                func = idaapi.get_func(xref.frm)
                if func:
                    func_name = idc.get_func_name(xref.frm)
                    f.write(f"  {xref_count}. From: 0x{xref.frm:X} in {func_name}\n")
                else:
                    f.write(f"  {xref_count}. From: 0x{xref.frm:X} (no function)\n")
            
            if xref_count == 0:
                f.write("  None\n")
            
            addr = found_addr + 1
    
    # Also search for "defbfm" (lowercase)
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("Searching for lowercase 'defbfm'...\n")
    f.write("=" * 80 + "\n\n")
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        f.write(f"Searching segment: {seg_name}\n")
        
        addr = seg_start
        while addr < seg_end:
            found_addr = idc.find_binary(addr, seg_end, "64 65 66 62 66 6D", 16, idc.SEARCH_DOWN)
            if found_addr == idaapi.BADADDR:
                break
            
            f.write(f"  Found at 0x{found_addr:X}\n")
            addr = found_addr + 1
    
    # Search for just "BFM" which might be part of filenames
    f.write("\n\n" + "=" * 80 + "\n")
    f.write("Searching for 'BFM' substring...\n")
    f.write("=" * 80 + "\n\n")
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_start = idc.get_segm_start(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        
        if "CODE" not in seg_name.upper():  # Only search data segments
            continue
        
        f.write(f"Searching segment: {seg_name}\n")
        
        addr = seg_start
        count = 0
        while addr < seg_end and count < 20:  # Limit to first 20 hits
            found_addr = idc.find_binary(addr, seg_end, "42 46 4D", 16, idc.SEARCH_DOWN)
            if found_addr == idaapi.BADADDR:
                break
            
            # Get surrounding bytes
            before = "".join([chr(idc.get_wide_byte(found_addr + i)) if 32 <= idc.get_wide_byte(found_addr + i) < 127 else '.' for i in range(-8, 0)])
            bfm = "BFM"
            after = "".join([chr(idc.get_wide_byte(found_addr + i)) if 32 <= idc.get_wide_byte(found_addr + i) < 127 else '.' for i in range(3, 11)])
            
            f.write(f"  0x{found_addr:X}: {before}{bfm}{after}\n")
            
            addr = found_addr + 1
            count += 1

print(f"Search complete: {output_file}")
idc.qexit(0)
