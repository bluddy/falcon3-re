"""
Extract callee functions from seed functions in IDA.

This script reads seeds from a JSON file and extracts all functions
they call (callees), generating a comprehensive report with caller counts.

Usage:
    idat.exe -A -S"extract_callees_generic.py <seeds_file>" FALCONCD.EXE.i64
    
Or default to flight_physics_seeds.json if no argument provided.
"""

import idc
import idaapi
import idautils
import json
import sys
from pathlib import Path

def load_seeds(seeds_filename=None):
    """Load seed functions from JSON file."""
    if seeds_filename is None:
        seeds_filename = "flight_physics_seeds.json"
    
    seeds_path = Path(__file__).parent.parent / seeds_filename
    
    if not seeds_path.exists():
        print(f"ERROR: {seeds_path} not found!")
        return {}
    
    with open(seeds_path, 'r') as f:
        data = json.load(f)
    
    # Convert to dict: address -> name
    seeds = {}
    for seed in data['seeds']:
        addr_str = seed['address']
        addr = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str, 16)
        seeds[addr] = seed['name']
    
    print(f"Loaded {len(seeds)} seed functions from {seeds_path}")
    return seeds

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
                    
                    # Skip self-references
                    if callee_addr == func_addr:
                        continue
                    
                    if callee_addr not in callees:
                        callee_name = idc.get_func_name(callee_addr)
                        callee_size = target_func.end_ea - target_func.start_ea
                        
                        callees[callee_addr] = {
                            'address': callee_addr,
                            'name': callee_name,
                            'size': callee_size,
                            'call_sites': [head]
                        }
                    else:
                        # Multiple calls to same function
                        callees[callee_addr]['call_sites'].append(head)
    
    return list(callees.values())

def get_caller_count(func_addr):
    """Count how many functions call this function."""
    callers = set()
    
    for xref in idautils.XrefsTo(func_addr, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Near call, Far call
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                callers.add(caller_func.start_ea)
    
    return len(callers)

def count_comparisons(func_addr):
    """Count comparison instructions in function (indicator of complexity)."""
    func = idaapi.get_func(func_addr)
    if not func:
        return 0
    
    comp_count = 0
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head)
        if mnem in ['cmp', 'test', 'jz', 'jnz', 'je', 'jne', 'jl', 'jg', 'jle', 'jge', 'ja', 'jb', 'jae', 'jbe']:
            comp_count += 1
    
    return comp_count

def is_already_documented(addr):
    """Check if function is already documented with a descriptive name."""
    name = idc.get_func_name(addr)
    return not (name.startswith('sub_') or name.startswith('loc_'))

def main():
    print("="*80)
    print("EXTRACTING CALLEES FROM FLIGHT PHYSICS FUNCTIONS")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    # Load seeds
    seeds = load_seeds()
    if not seeds:
        print("ERROR: No seeds loaded. Exiting.")
        idc.qexit(1)
        return
    
    all_callees = {}
    new_functions_map = {}  # addr -> info (dedupe across all seeds)
    
    for func_addr, func_name in sorted(seeds.items()):
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
                
                # Add to new functions map (dedupe)
                if addr not in new_functions_map:
                    new_functions_map[addr] = {
                        'address': addr,
                        'name': name,
                        'size': size,
                        'called_by': [func_name]
                    }
                else:
                    new_functions_map[addr]['called_by'].append(func_name)
        
        all_callees[func_name] = {
            'address': func_addr,
            'total_callees': len(callees),
            'documented': len(documented),
            'undocumented': len(undocumented),
            'callees': callees
        }
    
    # Analyze new functions in detail
    print("\n" + "="*80)
    print("ANALYZING NEW FUNCTIONS IN DETAIL")
    print("="*80)
    
    new_functions = []
    for addr, info in sorted(new_functions_map.items()):
        # Get additional metadata
        caller_count = get_caller_count(addr)
        comp_count = count_comparisons(addr)
        
        enhanced_info = {
            **info,
            'caller_count': caller_count,
            'comparison_count': comp_count,
            'called_by_count': len(info['called_by'])
        }
        new_functions.append(enhanced_info)
        
        print(f"{addr:#08x}: {info['name']:40} ({info['size']:4}B) "
              f"callers={caller_count:3} comps={comp_count:3} "
              f"seeds={len(info['called_by'])}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    total_callees = sum(c['total_callees'] for c in all_callees.values())
    total_documented = sum(c['documented'] for c in all_callees.values())
    total_new = len(new_functions)
    
    print(f"\nSeed functions analyzed: {len(seeds)}")
    print(f"Total callees found: {total_callees}")
    print(f"  Already documented: {total_documented}")
    print(f"  New unique functions: {total_new}")
    
    # Sort new functions by different criteria for reporting
    print(f"\n{'='*80}")
    print("TOP 15 NEW FUNCTIONS BY SIZE (complexity candidates)")
    print("="*80)
    by_size = sorted(new_functions, key=lambda x: x['size'], reverse=True)[:15]
    for i, f in enumerate(by_size, 1):
        print(f"{i:2}. {f['address']:#08x}: {f['name']:40} "
              f"({f['size']:4}B, {f['caller_count']:3} callers)")
    
    print(f"\n{'='*80}")
    print("TOP 15 NEW FUNCTIONS BY CALLER COUNT (utility candidates)")
    print("="*80)
    by_callers = sorted(new_functions, key=lambda x: x['caller_count'], reverse=True)[:15]
    for i, f in enumerate(by_callers, 1):
        print(f"{i:2}. {f['address']:#08x}: {f['name']:40} "
              f"({f['caller_count']:3} callers, {f['size']:4}B)")
    
    # Save report
    output_path = Path(__file__).parent.parent / "flight_physics_callees_report.json"
    report = {
        'timestamp': '2026-11-15',
        'seed_functions': len(seeds),
        'total_callees': total_callees,
        'documented': total_documented,
        'undocumented': total_new,
        'seeds': {hex(addr): name for addr, name in seeds.items()},
        'details': all_callees,
        'new_functions': new_functions
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Report saved to: {output_path}")
    print(f"Next step: Analyze the {total_new} new functions and name them!")
    print("="*80)
    
    # Exit
    idc.qexit(0)

if __name__ == "__main__":
    main()
