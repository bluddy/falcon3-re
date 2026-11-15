"""
Find references to PEOPLE.DAT to locate face loading code
"""
import idaapi
import idautils
import idc
import json

def search_for_string(search_str):
    """Search for a string in the binary"""
    results = []
    for s in idautils.Strings():
        str_val = str(s)
        if search_str.upper() in str_val.upper():
            results.append({
                'addr': s.ea,
                'hex_addr': f'0x{s.ea:X}',
                'string': str_val,
                'length': s.length
            })
    return results

def find_xrefs_to_addr(addr):
    """Find all cross-references to an address"""
    xrefs = []
    for xref in idautils.XrefsTo(addr, 0):
        func = idaapi.get_func(xref.frm)
        func_name = idc.get_func_name(xref.frm) if func else None
        xrefs.append({
            'from': xref.frm,
            'hex_from': f'0x{xref.frm:X}',
            'type': xref.type,
            'function': func_name,
            'disasm': idc.generate_disasm_line(xref.frm, 0)
        })
    return xrefs

def main():
    print("Searching for graphics file references...")
    
    # Search for common graphics files
    search_terms = [
        'PEOPLE', 'MONITOR', 'SYSMENU', 'MADFONT',
        'DAT', 'IDX', 'BUTTON'
    ]
    
    results = {}
    
    for term in search_terms:
        print(f"Searching for: {term}")
        matches = search_for_string(term)
        if matches:
            print(f"  Found {len(matches)} matches")
            for match in matches:
                # Find xrefs to this string
                xrefs = find_xrefs_to_addr(match['addr'])
                match['xrefs'] = xrefs
                print(f"    0x{match['addr']:X}: \"{match['string']}\" ({len(xrefs)} xrefs)")
            
            results[term] = matches
    
    # Save results
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\graphics_files_xrefs.json'
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print(f"Found {sum(len(v) for v in results.values())} total string matches")

if __name__ == '__main__':
    main()
    idc.qexit(0)
