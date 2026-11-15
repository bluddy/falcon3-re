"""
Sync the 211 new functions to IDA.
Simple focused script for the expansion batch.
"""
import idaapi
import idc
import re

def main():
    idaapi.auto_wait()
    
    print("=" * 80)
    print("SYNCING 211 NEW FUNCTIONS FROM EXPANSION ANALYSIS")
    print("=" * 80)
    
    # Read the new functions file
    import os
    yaml_path = os.path.join(os.path.dirname(__file__), '..', 'new_functions_expansion.yaml')
    print(f"Reading from: {yaml_path}")
    with open(yaml_path, 'r') as f:
        content = f.read()
    
    # Parse addresses and names
    functions = []
    lines = content.split('\n')
    
    current_func = {}
    for line in lines:
        if line.strip().startswith('- address:'):
            if current_func:
                functions.append(current_func)
            current_func = {}
            addr_str = line.split(':', 1)[1].strip()
            current_func['address'] = int(addr_str, 16)
        elif line.strip().startswith('name:'):
            name = line.split(':', 1)[1].strip()
            current_func['name'] = name
    
    if current_func:
        functions.append(current_func)
    
    print(f"\nFound {len(functions)} functions to sync")
    
    # Apply names
    renamed = 0
    already_named = 0
    failed = 0
    
    for func in functions:
        addr = func['address']
        new_name = func['name']
        
        # Check if function exists
        if not idc.get_func_attr(addr, idc.FUNCATTR_START):
            failed += 1
            continue
        
        # Get current name
        current_name = idc.get_func_name(addr)
        
        if current_name == new_name:
            already_named += 1
            continue
        
        # Rename
        if idc.set_name(addr, new_name, idc.SN_NOWARN | idc.SN_NOCHECK):
            renamed += 1
            if renamed <= 10:  # Show first 10
                print(f"  Renamed: 0x{addr:06X}: {current_name} -> {new_name}")
        else:
            failed += 1
            if failed <= 5:  # Show first 5 failures
                print(f"  FAILED: 0x{addr:06X}: {new_name}")
    
    print(f"\n" + "=" * 80)
    print("SYNC RESULTS")
    print("=" * 80)
    print(f"  Renamed: {renamed}")
    print(f"  Already correct: {already_named}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(functions)}")
    
    # Save summary
    summary_path = os.path.join(os.path.dirname(__file__), '..', 'ida_falconcd', 'sync_new_functions_result.txt')
    with open(summary_path, 'w') as f:
        f.write(f"Sync Results\n")
        f.write(f"============\n")
        f.write(f"Renamed: {renamed}\n")
        f.write(f"Already correct: {already_named}\n")
        f.write(f"Failed: {failed}\n")
        f.write(f"Total: {len(functions)}\n")
    
    print("\nDone!")
    
    idc.qexit(0)

if __name__ == '__main__':
    main()
