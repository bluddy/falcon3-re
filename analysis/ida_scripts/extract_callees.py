"""
Extract callee functions from specific functions in IDA.

This script takes a list of function addresses and extracts all functions
they call (callees), generating a report of new functions to document.

Usage:
    idat.exe -A -S"extract_callees.py" FALCONCD.EXE.i64
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

# Functions to analyze (from docs/architecture/ai.md)
TARGET_FUNCTIONS = {
    0x495DF: "ai_context_batch_processor",   # 16 callees
    0x3CE92: "ai_entity_behavior_dispatcher", # 25 callees
    0x3CFAA: "ai_behavior_state_machine",
    0x3D180: "ai_target_tracking_update",
    0x3D1C5: "ai_behavior_mirror_to_target",
    0x2703F: "ai_farptr_table_get",           # 78 callers (leaf)
}

def get_function_callees(func_addr):
    """Get all functions called by a given function using IDA xrefs."""
    callees = {}  # Use dict to auto-dedupe
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    # Iterate through all instructions in the function
    for head in idautils.Heads(func.start_ea, func.end_ea):
        # Get all code cross-references from this address
        for xref in idautils.XrefsFrom(head, 0):
            # Check if it's a call or jump to code
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Near call, Far call
                target = xref.to
                
                # Check if target is a valid function
                target_func = idaapi.get_func(target)
                if target_func:
                    callee_addr = target_func.start_ea
                    
                    # Skip self-references and jumps within same function
                    if callee_addr == func_addr:
                        continue
                    
                    if callee_addr not in callees:
                        callee_name = idc.get_func_name(callee_addr)
                        callee_size = target_func.end_ea - target_func.start_ea
                        
                        callees[callee_addr] = {
                            'address': callee_addr,
                            'name': callee_name,
                            'size': callee_size,
                            'call_site': head
                        }
    
    return list(callees.values())

def is_already_documented(addr):
    """Check if function is already documented with a descriptive name."""
    name = idc.get_func_name(addr)
    # If it starts with sub_ or loc_, it's not documented
    return not (name.startswith('sub_') or name.startswith('loc_'))

def main():
    print("="*80)
    print("EXTRACTING CALLEES FROM AI FUNCTIONS")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    all_callees = {}
    new_functions = []
    
    for func_addr, func_name in sorted(TARGET_FUNCTIONS.items()):
        print(f"\n{'='*80}")
        print(f"Function: {func_name} @ {func_addr:#08x}")
        print(f"{'='*80}")
        
        # Check if function exists
        func = idaapi.get_func(func_addr)
        if not func:
            print(f"  ERROR: Not a function!")
            continue
        
        # Get callees
        callees = get_function_callees(func_addr)
        print(f"  Found {len(callees)} unique callees")
        
        # Categorize
        documented = []
        undocumented = []
        
        for callee in callees:
            addr = callee['address']
            name = callee['name']
            size = callee['size']
            
            if is_already_documented(addr):
                documented.append(callee)
                print(f"    ✓ {name:40} @ {addr:#08x} ({size:4}B) - already documented")
            else:
                undocumented.append(callee)
                print(f"    • {name:40} @ {addr:#08x} ({size:4}B) - NEW")
                new_functions.append({
                    'address': addr,
                    'name': name,
                    'size': size,
                    'called_by': func_name,
                    'called_by_addr': func_addr
                })
        
        all_callees[func_name] = {
            'address': func_addr,
            'total_callees': len(callees),
            'documented': len(documented),
            'undocumented': len(undocumented),
            'callees': callees
        }
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_callees = sum(c['total_callees'] for c in all_callees.values())
    total_documented = sum(c['documented'] for c in all_callees.values())
    total_new = sum(c['undocumented'] for c in all_callees.values())
    
    print(f"\nTotal callees found: {total_callees}")
    print(f"  Already documented: {total_documented}")
    print(f"  New functions: {total_new}")
    
    if new_functions:
        print(f"\n{'='*80}")
        print("NEW FUNCTIONS TO DOCUMENT")
        print("="*80)
        
        # Group by caller
        by_caller = {}
        for nf in new_functions:
            caller = nf['called_by']
            if caller not in by_caller:
                by_caller[caller] = []
            by_caller[caller].append(nf)
        
        for caller, funcs in sorted(by_caller.items()):
            print(f"\nCalled by {caller}:")
            for f in sorted(funcs, key=lambda x: x['address']):
                print(f"  {f['address']:#08x}: {f['name']:40} ({f['size']:4}B)")
    
    # Save report
    output_path = Path(__file__).parent.parent / "ai_callees_report.json"
    report = {
        'timestamp': '2026-11-15',
        'target_functions': len(TARGET_FUNCTIONS),
        'total_callees': total_callees,
        'documented': total_documented,
        'undocumented': total_new,
        'details': all_callees,
        'new_functions': new_functions
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Report saved to: {output_path}")
    print("="*80)
    
    # Exit
    idc.qexit(0)

if __name__ == "__main__":
    main()
