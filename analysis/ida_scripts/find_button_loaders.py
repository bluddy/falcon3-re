"""
Find functions that load button graphics - these MUST decompress the data.

We have files: BUTTON1, BUTTON2, BUTTON3, BUTTOF1, BUTTOF2, BUTTOF3, BUTTOM1, etc.
Let's find code that references these strings and trace the decompression from there.

Run in IDA: File > Script file > find_button_loaders.py
"""

import idaapi
import idc
import idautils
import json

def find_string_references(search_str):
    """Find all references to a string."""
    refs = []
    
    # Search for strings
    for string_ea in idautils.Strings():
        s = str(string_ea)
        if search_str.upper() in s.upper():
            # Find xrefs to this string
            for xref in idautils.XrefsTo(string_ea.ea, 0):
                func = idaapi.get_func(xref.frm)
                if func:
                    refs.append({
                        'string': s,
                        'string_ea': f'0x{string_ea.ea:x}',
                        'xref_from': f'0x{xref.frm:x}',
                        'function': idc.get_func_name(func.start_ea),
                        'function_ea': f'0x{func.start_ea:x}'
                    })
    
    return refs

def analyze_function_for_decompression(func_ea):
    """Quick check if function might do decompression."""
    func = idaapi.get_func(func_ea)
    if not func:
        return {}
    
    loops = 0
    buffer_writes = 0
    rep_found = False
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head).lower()
        
        if mnem in ['loop', 'loopz', 'loopnz']:
            loops += 1
        
        if mnem == 'rep':
            rep_found = True
        
        if mnem in ['mov', 'stosb']:
            op0 = idc.print_operand(head, 0)
            if '[' in op0:
                buffer_writes += 1
    
    return {
        'loops': loops,
        'buffer_writes': buffer_writes,
        'has_rep': rep_found,
        'likely_decompressor': loops > 0 or rep_found
    }

def main():
    print("="*80)
    print("FINDING BUTTON GRAPHICS LOADERS")
    print("="*80)
    
    idaapi.auto_wait()
    
    # Search for button-related strings
    search_terms = ['BUTTON', 'BUTTO']
    
    all_refs = []
    for term in search_terms:
        print(f"\nSearching for: {term}")
        refs = find_string_references(term)
        all_refs.extend(refs)
        print(f"  Found {len(refs)} references")
    
    # Remove duplicates
    unique_funcs = {}
    for ref in all_refs:
        func_ea = int(ref['function_ea'], 16)
        if func_ea not in unique_funcs:
            unique_funcs[func_ea] = {
                'name': ref['function'],
                'address': ref['function_ea'],
                'strings': []
            }
        unique_funcs[func_ea]['strings'].append(ref['string'])
    
    print(f"\n{'='*80}")
    print(f"UNIQUE FUNCTIONS THAT REFERENCE BUTTON FILES:")
    print(f"{'='*80}")
    print(f"Found {len(unique_funcs)} unique functions\n")
    
    # Analyze each function
    results = []
    for func_ea, info in sorted(unique_funcs.items()):
        print(f"{info['name']:40s} @ {info['address']}")
        print(f"  Strings: {', '.join(set(info['strings']))}")
        
        # Analyze for decompression
        analysis = analyze_function_for_decompression(func_ea)
        info['analysis'] = analysis
        
        if analysis:
            print(f"  Loops: {analysis['loops']}, Buffer writes: {analysis['buffer_writes']}, Has REP: {analysis['has_rep']}")
            if analysis['likely_decompressor']:
                print(f"  >>> LIKELY DECOMPRESSOR! <<<")
        
        results.append(info)
        print()
    
    # Save results
    output_file = r'c:\Users\ybarnoy\projects\falcon3\analysis\button_loader_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"{'='*80}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*80}")
    
    # Recommendations
    if results:
        print(f"\n[RECOMMENDATION]")
        likely = [r for r in results if r.get('analysis', {}).get('likely_decompressor')]
        if likely:
            print(f"These {len(likely)} functions likely contain decompression:")
            for r in likely[:5]:
                print(f"  - {r['name']} @ {r['address']}")
            print(f"\nDisassemble these functions to find the RLE algorithm.")
        else:
            print(f"No obvious decompression patterns found.")
            print(f"The decompression may be in a helper function they call.")
            print(f"Next: Disassemble these loaders and trace their callees.")
    else:
        print(f"\n[NO BUTTON REFERENCES FOUND]")
        print(f"Try searching for other graphics files or menu names.")

if __name__ == '__main__':
    main()
