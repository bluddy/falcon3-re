"""
Simple approach: Find all functions with UI-like patterns
"""
import idaapi
import idautils
import idc
import json

def score_function_as_ui(func_ea):
    """Score a function's likelihood of being UI code"""
    func = idaapi.get_func(func_ea)
    if not func:
        return 0, {}
    
    func_size = func.end_ea - func.start_ea
    if func_size < 30:
        return 0, {}
    
    # Count various instruction types
    calls = 0
    data_refs = 0
    comparisons = 0
    loops = 0
    
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        
        if mnem in ['call', 'callf']:
            calls += 1
        elif mnem in ['cmp', 'test']:
            comparisons += 1
        elif mnem in ['loop', 'loope', 'loopne']:
            loops += 1
        
        # Check for memory operands (data access)
        for i in range(2):
            op_type = idc.get_operand_type(ea, i)
            if op_type == idc.o_mem:
                data_refs += 1
        
        ea = idc.next_head(ea, func.end_ea)
    
    # UI functions typically have lots of calls, comparisons, and data access
    score = calls * 2 + comparisons + data_refs
    
    return score, {
        'calls': calls,
        'comparisons': comparisons,
        'data_refs': data_refs,
        'loops': loops,
        'size': func_size
    }

def main():
    print("Scanning all functions for UI patterns...")
    
    results = []
    count = 0
    
    for func_ea in idautils.Functions():
        count += 1
        if count % 100 == 0:
            print(f"  Processed {count} functions...")
        
        func_name = idc.get_func_name(func_ea)
        score, stats = score_function_as_ui(func_ea)
        
        if score >= 50:  # Threshold for "interesting"
            results.append({
                'address': func_ea,
                'hex_addr': f'0x{func_ea:X}',
                'name': func_name,
                'score': score,
                'stats': stats
            })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\nTotal functions scanned: {count}")
    print(f"Functions with score >= 50: {len(results)}")
    print(f"\nTop 50 functions:")
    print("-"*80)
    
    for i, func in enumerate(results[:50]):
        print(f"{i+1:3d}. 0x{func['address']:06X} score={func['score']:4d} "
              f"{func['name']:40s} "
              f"(calls={func['stats']['calls']}, cmp={func['stats']['comparisons']}, "
              f"data={func['stats']['data_refs']})")
    
    # Save
    output_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_scripts\ui_functions_scored.json'
    with open(output_path, 'w') as f:
        json.dump(results[:100], f, indent=2)
    
    print(f"\nTop 100 saved to: {output_path}")

if __name__ == '__main__':
    main()
    idc.qexit(0)
