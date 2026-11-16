"""
Search for all string references in the R45 segment and related data.
We found:
- "SQUADRON"
- "PILOT INFORMATION"  
- "COMMS."
- "DONE"

Let's find all strings to fully identify this menu.
"""
import idaapi
import idautils
import idc

def find_all_strings_in_segment(seg_start, seg_end, seg_name):
    """Find all string references in a segment."""
    print(f"Searching for strings in {seg_name} (0x{seg_start:X} - 0x{seg_end:X})")
    strings_found = []
    
    for ea in range(seg_start, seg_end):
        # Check if this address has a string
        str_val = idc.get_strlit_contents(ea)
        if str_val:
            try:
                decoded = str_val.decode('ascii', errors='replace')
                # Filter out single chars and junk
                if len(decoded) > 2 and decoded.isprintable():
                    # Check for xrefs to this string
                    xrefs = list(idautils.DataRefsTo(ea))
                    strings_found.append({
                        "address": ea,
                        "value": decoded,
                        "length": len(str_val),
                        "xref_count": len(xrefs),
                        "xrefs": [hex(x) for x in xrefs[:5]]  # First 5 xrefs
                    })
            except:
                pass
    
    return strings_found

def search_data_segments_for_strings(target_strings):
    """Search data segments for specific strings."""
    print("\nSearching all data segments for menu-related strings...")
    results = []
    
    for seg_ea in idautils.Segments():
        seg = idaapi.getseg(seg_ea)
        seg_name = idaapi.get_segm_name(seg)
        
        # Skip code segments, focus on data
        if seg.type == idaapi.SEG_CODE:
            continue
        
        print(f"  Checking {seg_name}...")
        
        for ea in range(seg.start_ea, seg.end_ea):
            str_val = idc.get_strlit_contents(ea)
            if str_val:
                try:
                    decoded = str_val.decode('ascii', errors='replace')
                    # Check if it matches any of our target strings
                    for target in target_strings:
                        if target.lower() in decoded.lower():
                            xrefs = list(idautils.DataRefsTo(ea))
                            results.append({
                                "segment": seg_name,
                                "address": ea,
                                "value": decoded,
                                "match": target,
                                "xref_count": len(xrefs),
                                "xrefs": [hex(x) for x in xrefs[:5]]
                            })
                            print(f"    FOUND: '{decoded}' at 0x{ea:X} ({len(xrefs)} xrefs)")
                except:
                    pass
    
    return results

def search_all_menu_strings():
    """Comprehensive search for menu strings."""
    print("=== COMPREHENSIVE STRING SEARCH FOR R45 MENU ===\n")
    
    # Known R45 strings
    target_strings = [
        "SQUADRON", "PILOT", "COMMS", "DONE", "ROSTER",
        "SELECT", "CALLSIGN", "RANK", "MISSIONS", "KILLS",
        "INFORMATION", "STATUS", "READY", "AVAILABLE"
    ]
    
    results = search_data_segments_for_strings(target_strings)
    
    print(f"\n=== SUMMARY ===")
    print(f"Found {len(results)} matching strings")
    
    # Save results
    output_lines = []
    output_lines.append("=== R45 MENU STRINGS ===\n")
    
    for r in results:
        output_lines.append(f"0x{r['address']:X} ({r['segment']}): '{r['value']}'")
        output_lines.append(f"  Match: {r['match']}")
        output_lines.append(f"  Xrefs: {r['xref_count']} - {', '.join(r['xrefs'])}")
        output_lines.append("")
    
    output_path = r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\r45_strings_search.txt"
    with open(output_path, 'w') as f:
        f.write('\n'.join(output_lines))
    
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    search_all_menu_strings()
