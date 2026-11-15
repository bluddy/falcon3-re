"""
Extract undocumented callees from menu system functions.
Run in IDA: File > Script file > extract_menu_callees2.py
"""

import idaapi
import idc
import idautils
import json

def is_documented(func_ea):
    """Check if a function has a non-default name."""
    name = idc.get_func_name(func_ea)
    if not name:
        return False
    # sub_* names are undocumented
    if name.startswith('sub_') or name.startswith('nullsub_'):
        return False
    # j_* (jump thunks) are documented
    return True

def get_call_xrefs(func_ea):
    """Get all function calls from this function."""
    callees = set()
    func = idaapi.get_func(func_ea)
    if not func:
        return callees
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        # Get xrefs from this instruction
        for xref in idautils.XrefsFrom(head, 0):
            # Only code flow refs that are calls
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Near call, Far call
                target_func = idaapi.get_func(xref.to)
                if target_func:
                    callees.add(target_func.start_ea)
    
    return callees

def count_comparisons(func_ea):
    """Count comparison instructions in function."""
    count = 0
    func = idaapi.get_func(func_ea)
    if not func:
        return 0
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head).lower()
        if mnem in ['cmp', 'test', 'jz', 'jnz', 'je', 'jne', 'jg', 'jl', 
                    'jge', 'jle', 'ja', 'jb', 'jae', 'jbe', 'js', 'jns']:
            count += 1
    
    return count

def count_callers(func_ea):
    """Count how many functions call this one."""
    callers = set()
    for xref in idautils.XrefsTo(func_ea, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                callers.add(caller_func.start_ea)
    return len(callers)

def analyze_menu_callees():
    """Extract undocumented callees from menu system seeds."""
    
    # Load menu seeds
    seeds_file = r'c:\Users\ybarnoy\projects\falcon3\analysis\menu_seeds3.json'
    with open(seeds_file, 'r') as f:
        seeds = json.load(f)
    
    print(f"Analyzing {len(seeds)} menu seed functions...")
    
    # Collect all callees
    all_callees = set()
    for seed in seeds:
        addr = int(seed['address'], 16)
        callees = get_call_xrefs(addr)
        all_callees.update(callees)
        print(f"  {seed['name']:40s}: {len(callees):3d} callees")
    
    print(f"\nTotal unique callees: {len(all_callees)}")
    
    # Filter to undocumented functions
    undoc_callees = []
    for ea in all_callees:
        if not is_documented(ea):
            func = idaapi.get_func(ea)
            if func:
                name = idc.get_func_name(ea)
                size = func.end_ea - func.start_ea
                comp_count = count_comparisons(ea)
                caller_count = count_callers(ea)
                
                undoc_callees.append({
                    'address': f'0x{ea:x}',
                    'name': name,
                    'size': size,
                    'comparisons': comp_count,
                    'callers': caller_count
                })
    
    # Sort by callers (most called first), then by size
    undoc_callees.sort(key=lambda x: (x['callers'], x['size']), reverse=True)
    
    # Write results
    output_file = r'c:\Users\ybarnoy\projects\falcon3\analysis\menu_callees_report2.json'
    result = {
        'total_seeds': len(seeds),
        'total_callees': len(all_callees),
        'undocumented_callees': len(undoc_callees),
        'callees': undoc_callees
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✓ Found {len(undoc_callees)} undocumented callees")
    print(f"✓ Saved to: {output_file}")
    print("\nTop 10 by caller count:")
    for callee in undoc_callees[:10]:
        print(f"  {callee['address']:10s} {callee['name']:30s} "
              f"{callee['size']:4d}B  {callee['comparisons']:3d} cmps  "
              f"{callee['callers']:3d} callers")

if __name__ == '__main__':
    idaapi.auto_wait()
    analyze_menu_callees()
