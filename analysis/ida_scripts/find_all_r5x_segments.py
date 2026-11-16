#!/usr/bin/env python3
"""
Find all R5X menu overlay segments (R50-R59).
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Searching for all R5X menu segments...")
    print()
    
    r5x_segments = []
    
    for seg_ea in idautils.Segments():
        name = idc.get_segm_name(seg_ea)
        
        # Look for R5X pattern
        if name.startswith('R5') or name.startswith('R_5'):
            seg_end = idc.get_segm_end(seg_ea)
            seg_size = seg_end - seg_ea
            
            # Count functions
            func_count = 0
            for func_ea in idautils.Functions(seg_ea, seg_end):
                func_count += 1
            
            r5x_segments.append({
                'name': name,
                'start': hex(seg_ea),
                'end': hex(seg_end),
                'size': seg_size,
                'function_count': func_count
            })
            
            print(f"[+] {name}")
            print(f"    Range: 0x{seg_ea:X} - 0x{seg_end:X}")
            print(f"    Size: {seg_size} bytes (0x{seg_size:X})")
            print(f"    Functions: {func_count}")
            print()
    
    print(f"[+] Found {len(r5x_segments)} R5X segments")
    print()
    
    # Also look for "BRIEFING", "MISSION", "FLIGHT" strings
    print("[*] Searching for briefing-related strings...")
    
    briefing_strings = []
    keywords = [b'BRIEFING', b'MISSION', b'FLIGHT', b'TARGET', b'OBJECTIVE',
                b'ALTITUDE', b'SPEED', b'WAYPOINT', b'INGRESS', b'EGRESS']
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        ea = seg_ea
        seg_end = idc.get_segm_end(seg_ea)
        
        while ea < seg_end:
            str_type = idc.get_str_type(ea)
            if str_type is not None:
                string_val = idc.get_strlit_contents(ea)
                if string_val:
                    # Check if any keyword matches
                    for keyword in keywords:
                        if keyword in string_val.upper():
                            # Found a match, get xrefs
                            xrefs = list(idautils.XrefsTo(ea))
                            if xrefs:
                                briefing_strings.append({
                                    'string': string_val.decode('ascii', errors='ignore'),
                                    'addr': hex(ea),
                                    'segment': seg_name,
                                    'xref_count': len(xrefs),
                                    'xref_funcs': [idc.get_func_name(x.frm) for x in xrefs[:3]]
                                })
                            break
            
            ea = idc.next_head(ea, seg_end)
    
    print(f"[+] Found {len(briefing_strings)} briefing-related strings")
    for s in briefing_strings[:20]:
        print(f"    \"{s['string']}\" (segment: {s['segment']}, xrefs: {s['xref_count']})")
    print()
    
    # Save results
    result = {
        'r5x_segments': r5x_segments,
        'briefing_strings': briefing_strings
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\r5x_segments_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("[+] Results saved to analysis/r5x_segments_result.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
