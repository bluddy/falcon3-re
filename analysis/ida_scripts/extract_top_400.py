"""
Extract detailed info for Top 400 functions (ranks 301-400).
Generates full function details for analysis.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def get_function_xrefs_to(ea):
    """Count cross-references to a function."""
    count = 0
    for xref in idautils.XrefsTo(ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            count += 1
    return count

def get_function_calls(func_ea):
    """Get functions called by this function."""
    func = idaapi.get_func(func_ea)
    if not func:
        return []
    
    callees = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        if idc.print_insn_mnem(ea) in ['call', 'callf']:
            for xref in idautils.XrefsFrom(ea, 0):
                if xref.type in [idc.fl_CN, idc.fl_CF]:
                    target_name = idc.get_func_name(xref.to)
                    if target_name:
                        callees.append({
                            'address': hex(xref.to),
                            'name': target_name
                        })
                        break
        ea = idc.next_head(ea, func.end_ea)
    
    return callees

def analyze_function_category(name):
    """Categorize function by name pattern."""
    if name.startswith('sub_'):
        return 'uncategorized', 'Needs full analysis'
    elif name.startswith('utility_') or name.endswith('_utility'):
        return 'utility', 'Needs investigation'
    elif name.startswith('undoc_'):
        return 'undocumented', 'Has name but no docs'
    elif any(name.startswith(p) for p in ['overlay_bridge_to_', 'r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6']):
        return 'overlay', 'Overlay-specific'
    else:
        return 'categorized', 'Already done'

def main():
    print("="*70)
    print("EXTRACTING TOP 400 FUNCTIONS (Ranks 301-400)")
    print("="*70)
    
    idaapi.auto_wait()
    print("✓ Auto-analysis complete")
    
    # Get all functions sorted by xref count
    print("\nEnumerating all functions...")
    functions = []
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        xref_count = get_function_xrefs_to(func_ea)
        func_size = idc.get_func_attr(func_ea, idc.FUNCATTR_END) - func_ea
        
        functions.append({
            'address': func_ea,
            'name': func_name,
            'xrefs': xref_count,
            'size': func_size
        })
    
    print(f"✓ Found {len(functions)} total functions")
    
    # Sort by xrefs
    functions.sort(key=lambda x: x['xrefs'], reverse=True)
    
    # Extract ranks 301-400
    print("\nExtracting ranks 301-400...")
    top_400_functions = []
    
    for rank, func in enumerate(functions[300:400], 301):
        func_ea = func['address']
        func_name = func['name']
        
        # Get detailed info
        callees = get_function_calls(func_ea)
        category, status = analyze_function_category(func_name)
        
        entry = {
            'rank': rank,
            'address': func_ea,
            'hex_address': hex(func_ea),
            'name': func_name,
            'size': func['size'],
            'xrefs': func['xrefs'],
            'calls': len(callees),
            'callees': callees,
            'category': category,
            'status': status
        }
        
        top_400_functions.append(entry)
        
        if rank % 20 == 0:
            print(f"  Processed rank {rank}...")
    
    # Statistics
    needs_work = [f for f in top_400_functions if f['category'] in ['uncategorized', 'utility', 'undocumented']]
    
    print(f"\n{'='*70}")
    print("STATISTICS")
    print(f"{'='*70}")
    print(f"Total extracted: {len(top_400_functions)}")
    print(f"Needs work: {len(needs_work)}")
    print(f"Already done: {len(top_400_functions) - len(needs_work)}")
    
    print(f"\nCall range: {min(f['calls'] for f in top_400_functions)} - {max(f['calls'] for f in top_400_functions)}")
    print(f"XRef range: {min(f['xrefs'] for f in top_400_functions)} - {max(f['xrefs'] for f in top_400_functions)}")
    
    # Save results
    output = {
        'timestamp': '2026-11-15',
        'ranks': '301-400',
        'total': len(top_400_functions),
        'needs_work': len(needs_work),
        'functions': top_400_functions,
        'summary': {
            'uncategorized': len([f for f in top_400_functions if f['category'] == 'uncategorized']),
            'utility': len([f for f in top_400_functions if f['category'] == 'utility']),
            'undocumented': len([f for f in top_400_functions if f['category'] == 'undocumented']),
            'overlay': len([f for f in top_400_functions if f['category'] == 'overlay']),
            'categorized': len([f for f in top_400_functions if f['category'] == 'categorized'])
        }
    }
    
    output_file = Path(r'C:\Users\ybarnoy\projects\falcon3\analysis\top_400_functions.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Results saved to: {output_file}")
    print(f"\n{'='*70}")
    print("NEXT: Analyze the {0} functions that need work".format(len(needs_work)))
    print(f"{'='*70}")

if __name__ == '__main__':
    main()

idc.qexit(0)
