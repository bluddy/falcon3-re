"""
Extract Top 300 functions by call frequency and identify which need categorization.
This expands our analysis from Top 200 to Top 300 (100 new functions).
"""

import idc
import idaapi
import idautils
import json
from collections import defaultdict

def analyze_function_name(name):
    """Categorize function by name pattern."""
    if name.startswith('sub_'):
        return 'uncategorized'
    elif name.startswith('utility_') or name.endswith('_utility'):
        return 'needs_investigation'
    elif name.startswith('undoc_'):
        return 'undocumented'
    elif any(name.startswith(p) for p in ['r15_', 'r29_', 'r30_', 'r32_', 'r37_', 'r38_', 'r39_',
                                            'r46_', 'r48_', 'r49_', 'r4C_', 'r4E_', 'r4F_',
                                            'r52_', 'r53_', 'r54_', 'r55_', 'r57_', 'r59_',
                                            'r06_', 'r07_']):
        return 'overlay_specific'
    elif any(name.startswith(p) for p in ['ai_', 'menu_', 'ui_', 'game_', 'file_', 'fixed_', 
                                            'trig_', 'vec_', 'farobj_', 'entity_', 'dispatch_',
                                            'flag_', 'state_', 'overlay_', 'kb_', 'ems_',
                                            'signed_', 'mouse_', 'input_', 'text_',
                                            'campaign_', 'mission_', 'weapon_', 'graphics_',
                                            'string_', 'number_', 'data_', 'timing_',
                                            'score_', 'vector_']):
        return 'well_categorized'
    else:
        return 'descriptive'

def get_function_xrefs_to(ea):
    """Count cross-references to a function."""
    count = 0
    for xref in idautils.XrefsTo(ea, 0):
        if xref.type in [idc.fl_CN, idc.fl_CF]:
            count += 1
    return count

def main():
    print("="*70)
    print("EXTRACTING TOP 300 FUNCTIONS")
    print("="*70)
    
    # Get all functions sorted by xref count
    print("\nScanning all functions...")
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
    
    print(f"Found {len(functions)} total functions")
    
    # Sort by xref count descending
    functions.sort(key=lambda x: x['xrefs'], reverse=True)
    
    # Take top 300
    top_300 = functions[:300]
    
    # Categorize
    category_stats = defaultdict(list)
    
    for i, func in enumerate(top_300, 1):
        func['rank'] = i
        category = analyze_function_name(func['name'])
        func['category'] = category
        category_stats[category].append(func)
    
    # Print summary
    print(f"\n{'='*70}")
    print("TOP 300 CATEGORIZATION STATUS")
    print(f"{'='*70}")
    print(f"\nTotal functions: {len(top_300)}")
    print(f"\n{'Category':<25} {'Count':<8} {'Percentage'}")
    print("-" * 50)
    
    for category in sorted(category_stats.keys()):
        count = len(category_stats[category])
        pct = (count / len(top_300)) * 100
        status = "✓" if category not in ['uncategorized', 'needs_investigation', 'undocumented'] else "⚠"
        print(f"{status} {category:<23} {count:<8} {pct:5.1f}%")
    
    # Focus on ranks 201-300 (the new 100 functions)
    new_functions = [f for f in top_300 if f['rank'] > 200]
    new_categories = defaultdict(list)
    for f in new_functions:
        new_categories[f['category']].append(f)
    
    print(f"\n{'='*70}")
    print("RANKS 201-300 (NEW 100 FUNCTIONS)")
    print(f"{'='*70}")
    print(f"\n{'Category':<25} {'Count':<8} {'Percentage'}")
    print("-" * 50)
    
    for category in sorted(new_categories.keys()):
        count = len(new_categories[category])
        pct = (count / len(new_functions)) * 100
        status = "✓" if category not in ['uncategorized', 'needs_investigation', 'undocumented'] else "⚠"
        print(f"{status} {category:<23} {count:<8} {pct:5.1f}%")
    
    # Show problems in new batch
    new_problems = []
    for cat in ['uncategorized', 'needs_investigation', 'undocumented']:
        new_problems.extend(new_categories.get(cat, []))
    
    if new_problems:
        print(f"\n⚠ FUNCTIONS NEEDING WORK IN RANKS 201-300: {len(new_problems)}")
        print("\nFirst 30 that need attention:")
        for func in new_problems[:30]:
            print(f"  Rank #{func['rank']:3d}: 0x{func['address']:06X} - {func['name']:<40s} ({func['xrefs']:2d} calls, {func['size']:4d}B)")
    else:
        print(f"\n✓ All functions in ranks 201-300 already properly categorized!")
    
    # Output to file
    output = {
        'total': len(top_300),
        'top_200_status': {cat: len([f for f in funcs if f['rank'] <= 200]) 
                          for cat, funcs in category_stats.items()},
        'ranks_201_300_status': {cat: len(funcs) for cat, funcs in new_categories.items()},
        'new_problems': new_problems,
        'top_300': top_300
    }
    
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\top_300_status.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Detailed results saved to: {output_file}")
    
    print("\n" + "="*70)
    print(f"READY TO PROCESS: {len(new_problems)} functions need categorization")
    print("="*70)

if __name__ == '__main__':
    main()

idc.qexit(0)
