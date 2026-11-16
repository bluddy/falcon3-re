"""
Find PATCHES.IDX/DAT loader function.
"""

import idaapi
import idautils
import idc

def find_string_refs(search_strings):
    """Find all references to strings containing search terms."""
    results = {}
    
    # Iterate through all strings in the database
    for string_ea in idautils.Strings():
        str_text = str(string_ea)
        
        # Check if any search string matches
        for search in search_strings:
            if search.upper() in str_text.upper():
                ea = string_ea.ea
                print(f"Found string at 0x{ea:X}: {repr(str_text)}")
                
                # Find xrefs to this string
                xrefs = list(idautils.XrefsTo(ea))
                if xrefs:
                    results[ea] = {
                        'string': str_text,
                        'xrefs': []
                    }
                    for xref in xrefs:
                        func = idaapi.get_func(xref.frm)
                        func_name = idc.get_func_name(func.start_ea) if func else "???"
                        print(f"  Referenced by 0x{xref.frm:X} in function {func_name} at 0x{func.start_ea if func else 0:X}")
                        results[ea]['xrefs'].append({
                            'addr': xref.frm,
                            'func': func.start_ea if func else 0,
                            'func_name': func_name
                        })
                break
    
    return results

def main():
    idaapi.auto_wait()
    
    print("Searching for PATCHES file references...")
    print("="*80)
    
    search_terms = ["PATCHES", "HPATCHES", "MPATCHES", "FGENBMAP", "GENBMAP", "MGENBMAP"]
    
    results = find_string_refs(search_terms)
    
    print("\n" + "="*80)
    print(f"Found {len(results)} string(s)")
    
    # Summarize unique functions
    unique_funcs = set()
    for string_ea, data in results.items():
        for xref in data['xrefs']:
            if xref['func'] != 0:
                unique_funcs.add((xref['func'], xref['func_name']))
    
    print(f"\nUnique loader functions ({len(unique_funcs)}):")
    for func_addr, func_name in sorted(unique_funcs):
        print(f"  0x{func_addr:X}: {func_name}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
