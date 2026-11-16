"""
Generate final Top 200 categorization status after all renamings.
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
    elif any(name.startswith(p) for p in ['r15_', 'r29_', 'r30_', 'r32_', 'r37_', 'r38_', 'r39_',
                                            'r46_', 'r48_', 'r49_', 'r4C_', 'r4E_', 'r4F_',
                                            'r52_', 'r53_', 'r54_', 'r55_', 'r57_', 'r59_']):
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
    print("FINAL TOP 200 CATEGORIZATION STATUS")
    print("="*70)
    
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
    
    # Print summary
    print(f"\nTotal functions analyzed: {len(top_200)}")
    print(f"\n{'Category':<25} {'Count':<8} {'Percentage'}")
    print("-" * 50)
    
    for category in sorted(category_stats.keys()):
        count = len(category_stats[category])
        pct = (count / len(top_200)) * 100
        status = "✓" if category not in ['uncategorized', 'needs_investigation'] else "✗"
        print(f"{status} {category:<23} {count:<8} {pct:5.1f}%")
    
    # Show any remaining problems
    problems = category_stats.get('uncategorized', []) + category_stats.get('needs_investigation', [])
    
    if problems:
        print(f"\n⚠ REMAINING ISSUES ({len(problems)} functions):")
        for func in problems[:20]:
            print(f"  Rank #{func['rank']:3d}: 0x{func['address']:06X} - {func['name']}")
    else:
        print(f"\n✓✓✓ NO REMAINING ISSUES! ALL 200 FUNCTIONS PROPERLY CATEGORIZED! ✓✓✓")
    
    # Output to file
    output = {
        'total': len(top_200),
        'summary': {cat: len(funcs) for cat, funcs in category_stats.items()},
        'categories': dict(category_stats),
        'top_200': top_200,
        'problems': problems
    }
    
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\final_top200_status.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Detailed results saved to: {output_file}")
    
    print("\n" + "="*70)
    if not problems:
        print("🎯 MISSION ACCOMPLISHED: TOP 200 CATEGORIZATION 100% COMPLETE!")
    else:
        print(f"⚠ {len(problems)} functions still need attention")
    print("="*70)

if __name__ == '__main__':
    main()

idc.qexit(0)
