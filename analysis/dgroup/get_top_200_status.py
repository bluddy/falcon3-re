"""
Extract current names and metadata for Top 200 functions to assess categorization status.
"""

import idc
import idaapi
import idautils
import json
from collections import defaultdict

def get_function_xrefs_to(ea):
    """Count cross-references to a function."""
    count = 0
    for xref in idautils.XrefsTo(ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:  # Call near/far
            count += 1
    return count

def analyze_function_name(name):
    """Categorize function by name pattern."""
    if name.startswith('sub_'):
        return 'uncategorized'
    elif name.startswith('utility_') or name.endswith('_utility'):
        return 'needs_investigation'
    elif any(name.startswith(p) for p in ['r15_', 'r29_', 'r48_', 'r53_', 'r55_', 'r57_']):
        return 'overlay_specific'
    elif any(name.startswith(p) for p in ['ai_', 'menu_', 'ui_', 'game_', 'file_', 'fixed_', 
                                            'trig_', 'vec_', 'farobj_', 'entity_', 'dispatch_',
                                            'flag_', 'state_', 'overlay_', 'kb_', 'ems_']):
        return 'well_categorized'
    else:
        return 'descriptive'

def main():
    print("Extracting Top 200 function metadata...")
    
    # Get all functions sorted by xref count
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
    
    # Sort by xref count descending
    functions.sort(key=lambda x: x['xrefs'], reverse=True)
    
    # Take top 200
    top_200 = functions[:200]
    
    # Categorize
    category_stats = defaultdict(list)
    
    for i, func in enumerate(top_200, 1):
        func['rank'] = i
        category = analyze_function_name(func['name'])
        func['category'] = category
        category_stats[category].append(func)
    
    # Output results
    output = {
        'total': len(top_200),
        'summary': {cat: len(funcs) for cat, funcs in category_stats.items()},
        'categories': dict(category_stats),
        'top_200': top_200
    }
    
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\top_200_current_status.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n=== Top 200 Categorization Status ===")
    print(f"Total functions: {len(top_200)}")
    print(f"\nCategory breakdown:")
    for category in sorted(category_stats.keys()):
        count = len(category_stats[category])
        pct = (count / len(top_200)) * 100
        print(f"  {category:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Show examples of needs_investigation
    print(f"\n=== Functions Needing Investigation (First 20) ===")
    needs_inv = category_stats.get('needs_investigation', [])
    for func in needs_inv[:20]:
        print(f"  Rank #{func['rank']:3d}: 0x{func['address']:06X} - {func['name']:40s} ({func['xrefs']:3d} calls, {func['size']:4d}B)")
    
    # Show uncategorized
    print(f"\n=== Uncategorized Functions (First 20) ===")
    uncat = category_stats.get('uncategorized', [])
    for func in uncat[:20]:
        print(f"  Rank #{func['rank']:3d}: 0x{func['address']:06X} - {func['name']:40s} ({func['xrefs']:3d} calls, {func['size']:4d}B)")
    
    print(f"\n✓ Results saved to: {output_file}")

if __name__ == '__main__':
    main()
