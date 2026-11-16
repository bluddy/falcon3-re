#!/usr/bin/env python3
"""
Dump all strings referenced by R52 flight briefing menu.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Searching for strings in R52 segment and references...")
    
    # Find R52 segment
    r52_start = None
    r52_end = None
    
    for seg_ea in idautils.Segments():
        name = idc.get_segm_name(seg_ea)
        if "R52" in name:
            r52_start = seg_ea
            r52_end = idc.get_segm_end(seg_ea)
            print(f"[+] Found R52 segment: {name} (0x{r52_start:X} - 0x{r52_end:X})")
            break
    
    if not r52_start:
        print("[!] R52 segment not found")
        idc.qexit(1)
    
    # Find all xrefs from R52 code to strings
    strings_found = {}
    
    ea = r52_start
    while ea < r52_end:
        # Check xrefs from this address
        for xref in idautils.XrefsFrom(ea, 0):
            target = xref.to
            
            # Check if target is a string
            str_type = idc.get_str_type(target)
            if str_type is not None:
                string_val = idc.get_strlit_contents(target)
                if string_val:
                    string_key = string_val.decode('ascii', errors='ignore')
                    if string_key not in strings_found:
                        strings_found[string_key] = []
                    
                    strings_found[string_key].append({
                        'from_addr': hex(ea),
                        'string_addr': hex(target),
                        'function': idc.get_func_name(ea)
                    })
        
        ea = idc.next_head(ea, r52_end)
    
    print(f"[+] Found {len(strings_found)} unique strings")
    print()
    
    # Print strings sorted by first reference
    for string, refs in sorted(strings_found.items(), key=lambda x: x[1][0]['from_addr']):
        print(f"String: \"{string}\"")
        print(f"  At: {refs[0]['string_addr']}")
        print(f"  Referenced from: {refs[0]['from_addr']} in {refs[0]['function']}")
        if len(refs) > 1:
            print(f"  ({len(refs)} total references)")
        print()
    
    # Save results
    result = {
        'string_count': len(strings_found),
        'strings': [
            {
                'string': string,
                'references': refs
            }
            for string, refs in strings_found.items()
        ]
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\r52_strings.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[+] Saved to analysis/r52_strings.json")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
