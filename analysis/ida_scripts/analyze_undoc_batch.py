"""
Analyze a batch of undocumented functions by rank.

Usage:
    idat.exe -A -S"analyze_undoc_batch.py 151 250" FALCONCD.EXE.i64
"""

import idc
import idaapi
import idautils
import json
import sys
from pathlib import Path

# Default range if no args
START_RANK = 701
END_RANK = 750

def get_caller_count(func_addr):
    callers = set()
    for xref in idautils.XrefsTo(func_addr, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                callers.add(caller_func.start_ea)
    return len(callers)

def count_comparisons(func_addr):
    func = idaapi.get_func(func_addr)
    if not func:
        return 0
    comp_count = 0
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head)
        if mnem in ['cmp', 'test', 'jz', 'jnz', 'je', 'jne', 'jl', 'jg', 'jle', 'jge', 'ja', 'jb', 'jae', 'jbe']:
            comp_count += 1
    return comp_count

def main():
    start = START_RANK - 1  # 0-indexed
    end = END_RANK
    
    print("="*80)
    print(f"ANALYZING UNDOCUMENTED FUNCTIONS {start+1}-{end}")
    print("="*80)
    
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    # Find all undocumented
    undocumented = []
    for func_ea in idautils.Functions():
        func_name = idc.get_func_name(func_ea)
        if func_name.startswith('sub_') or func_name.startswith('loc_'):
            func = idaapi.get_func(func_ea)
            size = func.end_ea - func.start_ea if func else 0
            undocumented.append({
                'address': func_ea,
                'name': func_name,
                'size': size
            })
    
    print(f"Total undocumented: {len(undocumented)}")
    
    # Sort and take requested batch
    sorted_funcs = sorted(undocumented, key=lambda x: x['size'], reverse=True)
    batch = sorted_funcs[start:end]
    
    print(f"Analyzing {len(batch)} functions (ranks {start+1}-{end})...")
    
    # Analyze
    analyzed = []
    for i, func in enumerate(batch, start+1):
        if i % 10 == 1 or i == end:
            print(f"[{i}/{end}] {func['name']}")
        
        addr = func['address']
        caller_count = get_caller_count(addr)
        comp_count = count_comparisons(addr)
        
        analyzed.append({
            **func,
            'caller_count': caller_count,
            'comparison_count': comp_count
        })
    
    # Save
    output_path = Path(__file__).parent.parent / f"undocumented_{start+1}_{end}_analysis.json"
    with open(output_path, 'w') as f:
        json.dump({'functions': analyzed}, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Analyzed {len(analyzed)} functions")
    print(f"Size range: {analyzed[0]['size']}B to {analyzed[-1]['size']}B")
    print(f"High reuse (5+ callers): {len([f for f in analyzed if f['caller_count'] >= 5])}")
    print(f"Report: {output_path}")
    print("="*80)
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
