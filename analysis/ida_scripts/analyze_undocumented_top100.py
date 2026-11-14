"""
Analyze top 100 largest undocumented functions in IDA.

Usage:
    idat.exe -A -S"analyze_undocumented_top100.py" FALCONCD.EXE.i64
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def get_caller_count(func_addr):
    """Count how many functions call this function."""
    callers = set()
    for xref in idautils.XrefsTo(func_addr, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                callers.add(caller_func.start_ea)
    return len(callers)

def get_function_callees(func_addr):
    """Get functions called by this function."""
    callees = []
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                target_func = idaapi.get_func(xref.to)
                if target_func and target_func.start_ea != func_addr:
                    callee_name = idc.get_func_name(target_func.start_ea)
                    if callee_name not in [c['name'] for c in callees]:
                        callees.append({
                            'address': target_func.start_ea,
                            'name': callee_name
                        })
    return callees

def count_comparisons(func_addr):
    """Count comparison instructions."""
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
    print("="*80)
    print("ANALYZING TOP 100 LARGEST UNDOCUMENTED FUNCTIONS")
    print("="*80)
    
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    # Find all undocumented functions
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
    
    print(f"\nTotal undocumented functions: {len(undocumented)}")
    
    # Sort by size and take top 100
    top100 = sorted(undocumented, key=lambda x: x['size'], reverse=True)[:100]
    
    # Analyze each
    analyzed = []
    for i, func in enumerate(top100, 1):
        addr = func['address']
        if i <= 10 or i > 90:  # Print first 10 and last 10
            print(f"[{i}/100] Analyzing {func['name']} @ {addr:#08x} ({func['size']}B)...")
        elif i == 11:
            print(f"... analyzing functions 11-90 ...")
        
        caller_count = get_caller_count(addr)
        callees = get_function_callees(addr)
        comp_count = count_comparisons(addr)
        
        analysis = {
            **func,
            'caller_count': caller_count,
            'callees': callees,
            'callee_count': len(callees),
            'comparison_count': comp_count
        }
        analyzed.append(analysis)
    
    # Save report
    output_path = Path(__file__).parent.parent / "undocumented_top100_analysis.json"
    report = {
        'timestamp': '2026-11-15',
        'total_undocumented': len(undocumented),
        'analyzed': 100,
        'functions': analyzed
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Analysis saved to: {output_path}")
    print("="*80)
    
    # Summary
    print(f"\nTOP 100 SUMMARY:")
    print(f"Size range: {analyzed[0]['size']}B to {analyzed[-1]['size']}B")
    print(f"Total size: {sum(f['size'] for f in analyzed)}B")
    
    # Functions 51-100
    next50 = analyzed[50:100]
    print(f"\nFUNCTIONS 51-100 (next batch):")
    print(f"Size range: {next50[0]['size']}B to {next50[-1]['size']}B")
    print(f"Total size: {sum(f['size'] for f in next50)}B")
    
    print(f"\nBy caller count (next 50):")
    by_callers = sorted(next50, key=lambda x: x['caller_count'], reverse=True)[:15]
    for i, f in enumerate(by_callers, 1):
        print(f"  {i:2}. {f['name']:20} - {f['caller_count']:3} callers ({f['size']:4}B)")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
