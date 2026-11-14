#!/usr/bin/env python3
"""
Analyze old registry/naming.yaml to find functions we can merge.

Compares old registry (IDA names like sub_16FDD) with new registry (hex addresses)
and identifies non-overlapping functions that can be rescued.
"""

import re
from pathlib import Path

def parse_simple_yaml(yaml_path):
    """Simple YAML parser for our function registry format."""
    with open(yaml_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    functions = []
    current_func = {}
    in_notes = False
    notes_lines = []
    
    for line in lines:
        line = line.rstrip('\n\r')
        
        # Skip schema and symbols header
        if line.startswith('schema:') or line.startswith('symbols:'):
            continue
        
        # New function entry (starts with "- ida:" or "  - address:")
        if line.startswith('- ida:') or line.startswith('  - address:'):
            # Save previous function
            if current_func:
                if notes_lines:
                    current_func['notes'] = ' '.join(notes_lines)
                    notes_lines = []
                functions.append(current_func)
            current_func = {}
            in_notes = False
            
            # Parse IDA name or address
            if line.startswith('- ida:'):
                current_func['ida'] = line.split(':', 1)[1].strip()
            else:
                addr_str = line.split(':', 1)[1].strip()
                current_func['address'] = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str)
        
        # Parse other fields
        elif line.startswith('  ') and ':' in line:
            # Check if it's a continuation of notes
            if in_notes and not any(line.strip().startswith(k + ':') for k in ['name', 'kind', 'sig', 'notes', 'size', 'system', 'doc']):
                notes_lines.append(line.strip())
            else:
                key = line.split(':', 1)[0].strip()
                value = line.split(':', 1)[1].strip() if ':' in line else ''
                
                if key == 'notes':
                    in_notes = True
                    if value:
                        notes_lines.append(value)
                elif key == 'size':
                    current_func[key] = int(value)
                else:
                    current_func[key] = value
                    in_notes = False
    
    # Add last function
    if current_func:
        if notes_lines:
            current_func['notes'] = ' '.join(notes_lines)
        functions.append(current_func)
    
    return functions

def extract_address_from_ida_name(ida_name):
    """Extract hex address from IDA name like sub_16FDD -> 0x16FDD."""
    match = re.match(r'sub_([0-9A-Fa-f]+)', ida_name)
    if match:
        return int(match.group(1), 16)
    return None

def main():
    repo_root = Path(__file__).parent.parent
    old_registry_path = repo_root / "registry" / "naming.yaml"
    new_registry_path = repo_root / "registry" / "functions.yaml"
    
    print("="*80)
    print("ANALYZING OLD REGISTRY FOR MERGE")
    print("="*80)
    
    # Load old registry
    print("\nLoading old registry...")
    old_functions = parse_simple_yaml(old_registry_path)
    old_funcs_only = [f for f in old_functions if f.get('kind') == 'function']
    print(f"  Found {len(old_funcs_only)} functions in old registry")
    
    # Load new registry
    print("\nLoading new registry...")
    new_functions = parse_simple_yaml(new_registry_path)
    print(f"  Found {len(new_functions)} functions in new registry")
    
    # Extract addresses from old registry (from IDA names)
    print("\nExtracting addresses from old registry IDA names...")
    old_with_addresses = []
    for func in old_funcs_only:
        if 'ida' in func:
            addr = extract_address_from_ida_name(func['ida'])
            if addr:
                func['address'] = addr
                old_with_addresses.append(func)
    print(f"  Extracted {len(old_with_addresses)} addresses from IDA names")
    
    # Build set of new addresses
    new_addresses = {f['address'] for f in new_functions}
    print(f"\nNew registry has {len(new_addresses)} unique addresses")
    
    # Find non-overlapping functions
    print("\nFinding non-overlapping functions...")
    non_overlapping = []
    overlapping = []
    for func in old_with_addresses:
        addr = func['address']
        if addr in new_addresses:
            overlapping.append(func)
        else:
            non_overlapping.append(func)
    
    print(f"  Overlapping: {len(overlapping)} functions (already in new registry)")
    print(f"  Non-overlapping: {len(non_overlapping)} functions (can be merged)")
    
    # Show overlapping functions
    if overlapping:
        print("\n" + "="*80)
        print("OVERLAPPING FUNCTIONS (verify names match):")
        print("="*80)
        for func in overlapping[:10]:  # Show first 10
            addr = func['address']
            old_name = func.get('name', 'UNKNOWN')
            # Find matching new function
            new_func = next((f for f in new_functions if f['address'] == addr), None)
            new_name = new_func['name'] if new_func else 'NOT FOUND'
            match = "OK" if old_name == new_name else "DIFF"
            print(f"[{match:4}] {addr:#08x}: old={old_name:40} new={new_name}")
        if len(overlapping) > 10:
            print(f"... and {len(overlapping) - 10} more")
    
    # Show some non-overlapping functions
    print("\n" + "="*80)
    print("NON-OVERLAPPING FUNCTIONS (sample - can be merged):")
    print("="*80)
    for func in non_overlapping[:20]:  # Show first 20
        addr = func['address']
        name = func.get('name', 'UNKNOWN')
        notes = func.get('notes', '')[:60]
        print(f"  {addr:#08x}: {name:35} - {notes}")
    if len(non_overlapping) > 20:
        print(f"... and {len(non_overlapping) - 20} more")
    
    # Statistics
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Old registry functions: {len(old_funcs_only)}")
    print(f"  With extractable addresses: {len(old_with_addresses)}")
    print(f"  Without addresses: {len(old_funcs_only) - len(old_with_addresses)}")
    print(f"\nNew registry functions: {len(new_functions)}")
    print(f"\nOverlapping: {len(overlapping)}")
    print(f"Non-overlapping (can merge): {len(non_overlapping)}")
    print(f"\nPotential new registry size: {len(new_functions) + len(non_overlapping)}")
    print("="*80)
    
    # Save analysis
    output_path = repo_root / "analysis" / "old_registry_analysis.txt"
    with open(output_path, 'w') as f:
        f.write(f"Total old functions: {len(old_funcs_only)}\n")
        f.write(f"With addresses: {len(old_with_addresses)}\n")
        f.write(f"Overlapping: {len(overlapping)}\n")
        f.write(f"Non-overlapping: {len(non_overlapping)}\n")
        f.write(f"\nNon-overlapping functions:\n")
        f.write("="*80 + "\n")
        for func in sorted(non_overlapping, key=lambda f: f['address']):
            addr = func['address']
            name = func.get('name', 'UNKNOWN')
            notes = func.get('notes', '')
            sig = func.get('sig', '')
            f.write(f"\n{addr:#08x}: {name}\n")
            if sig:
                f.write(f"  sig: {sig}\n")
            if notes:
                f.write(f"  notes: {notes}\n")
    
    print(f"\nDetailed analysis saved to: {output_path}")

if __name__ == "__main__":
    main()
