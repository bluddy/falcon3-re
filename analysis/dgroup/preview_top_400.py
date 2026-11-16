"""
Preview what Top 400 expansion would look like.
Quick check of ranks 301-400.
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
    elif any(name.startswith(p) for p in ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9']):
        return 'overlay_specific'
    elif any(name.startswith(p) for p in ['ai_', 'menu_', 'ui_', 'game_', 'file_', 'fixed_', 
                                            'trig_', 'vec_', 'farobj_', 'entity_', 'dispatch_',
                                            'flag_', 'state_', 'overlay_', 'kb_', 'ems_',
                                            'signed_', 'mouse_', 'input_', 'text_',
                                            'campaign_', 'mission_', 'weapon_', 'graphics_',
                                            'string_', 'number_', 'data_', 'timing_',
                                            'score_', 'vector_', 'font_']):
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
    print("TOP 400 PREVIEW - Ranks 301-400")
    print("="*70)
    
    idaapi.auto_wait()
    
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
    
    functions.sort(key=lambda x: x['xrefs'], reverse=True)
    
    # Get ranks 301-400
    ranks_301_400 = functions[300:400]
    
    # Categorize
    category_stats = defaultdict(list)
    for i, func in enumerate(ranks_301_400, 301):
        func['rank'] = i
        category = analyze_function_name(func['name'])
        func['category'] = category
        category_stats[category].append(func)
    
    # Print summary
    print(f"\n{'='*70}")
    print("RANKS 301-400 CATEGORIZATION STATUS")
    print(f"{'='*70}")
    print(f"\nTotal: {len(ranks_301_400)} functions")
    print(f"\n{'Category':<25} {'Count':<8} {'Percentage'}")
    print("-" * 50)
    
    for category in sorted(category_stats.keys()):
        count = len(category_stats[category])
        pct = (count / len(ranks_301_400)) * 100
        status = "✓" if category not in ['uncategorized', 'needs_investigation', 'undocumented'] else "⚠"
        print(f"{status} {category:<23} {count:<8} {pct:5.1f}%")
    
    # Show problems
    problems = []
    for cat in ['uncategorized', 'needs_investigation', 'undocumented']:
        problems.extend(category_stats.get(cat, []))
    
    print(f"\n{'='*70}")
    print(f"WORK NEEDED: {len(problems)} functions")
    print(f"{'='*70}")
    
    if problems:
        print("\nFirst 20 that need work:")
        for func in problems[:20]:
            print(f"  Rank #{func['rank']:3d}: 0x{func['address']:06X} - {func['name']:<40s} ({func['xrefs']:2d} calls, {func['size']:4d}B)")
    
    # Save preview
    output = {
        'total': len(ranks_301_400),
        'categories': {cat: len(funcs) for cat, funcs in category_stats.items()},
        'work_needed': len(problems),
        'problems': problems[:20],  # Just first 20
        'call_range': {
            'min': min(f['xrefs'] for f in ranks_301_400),
            'max': max(f['xrefs'] for f in ranks_301_400),
            'avg': sum(f['xrefs'] for f in ranks_301_400) // len(ranks_301_400)
        }
    }
    
    output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\top_400_preview.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Preview saved to: {output_file}")
    
    print("\n" + "="*70)
    print(f"RECOMMENDATION: {'GO FOR IT!' if len(problems) < 50 else 'Consider effort vs. benefit'}")
    print(f"Effort estimate: {len(problems)} functions to analyze")
    print("="*70)

if __name__ == '__main__':
    main()

idc.qexit(0)
