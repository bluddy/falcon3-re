#!/usr/bin/env python3
"""
Merge old registry/naming.yaml into new registry/functions.yaml.

Strategy:
1. Keep all new registry functions (our descriptive names are better)
2. Add all non-overlapping functions from old registry
3. For overlapping functions: keep new name, add old name as alias in notes
4. Sort by address for maintainability
"""

import re
from pathlib import Path
from datetime import datetime

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
        
        # Skip empty lines
        if not line.strip():
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
        elif line.strip() and ':' in line:
            # Check if it's a continuation of notes
            if in_notes and not any(line.strip().startswith(k + ':') for k in ['name', 'kind', 'sig', 'notes', 'size', 'system', 'doc', 'source']):
                notes_lines.append(line.strip())
            else:
                key = line.split(':', 1)[0].strip()
                value = line.split(':', 1)[1].strip() if ':' in line else ''
                
                if key == 'notes':
                    in_notes = True
                    if value:
                        notes_lines.append(value)
                elif key == 'size':
                    if value:
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

def format_function_yaml(func):
    """Format a function entry as YAML."""
    lines = []
    lines.append(f"  - address: {func['address']:#08x}")
    lines.append(f"    name: {func['name']}")
    
    if 'system' in func:
        lines.append(f"    system: {func['system']}")
    
    if 'size' in func:
        lines.append(f"    size: {func['size']}")
    
    # doc field (our new registry) or notes field (old registry)
    doc_text = func.get('doc', func.get('notes', ''))
    if doc_text:
        # Truncate if too long
        if len(doc_text) > 200:
            doc_text = doc_text[:197] + '...'
        lines.append(f"    doc: {doc_text}")
    
    if 'source' in func:
        lines.append(f"    source: {func['source']}")
    elif 'old_name' in func:
        lines.append(f"    source: old_registry (was: {func['old_name']})")
    
    return '\n'.join(lines)

def main():
    repo_root = Path(__file__).parent.parent
    old_registry_path = repo_root / "registry" / "naming.yaml"
    new_registry_path = repo_root / "registry" / "functions.yaml"
    merged_path = repo_root / "registry" / "functions_merged.yaml"
    
    print("="*80)
    print("MERGING OLD AND NEW REGISTRIES")
    print("="*80)
    
    # Load old registry
    print("\nLoading old registry...")
    old_functions = parse_simple_yaml(old_registry_path)
    old_funcs_only = [f for f in old_functions if f.get('kind') == 'function']
    print(f"  Found {len(old_funcs_only)} functions in old registry")
    
    # Extract addresses from old registry
    old_with_addresses = []
    for func in old_funcs_only:
        if 'ida' in func:
            addr = extract_address_from_ida_name(func['ida'])
            if addr:
                func['address'] = addr
                old_with_addresses.append(func)
    print(f"  Extracted {len(old_with_addresses)} addresses from IDA names")
    
    # Load new registry
    print("\nLoading new registry...")
    new_functions = parse_simple_yaml(new_registry_path)
    print(f"  Found {len(new_functions)} functions in new registry")
    
    # Build merged registry
    print("\nMerging...")
    merged = {}
    
    # First, add all new registry functions (priority)
    for func in new_functions:
        if 'address' not in func:
            continue  # Skip non-function entries
        addr = func['address']
        merged[addr] = func.copy()
    
    print(f"  Added {len(merged)} functions from new registry")
    
    # Then, add non-overlapping from old registry
    added_count = 0
    overlapping_count = 0
    for func in old_with_addresses:
        addr = func['address']
        if addr in merged:
            # Overlapping - add old name to notes if different
            overlapping_count += 1
            old_name = func.get('name', 'unknown')
            new_name = merged[addr]['name']
            if old_name != new_name:
                # Store old name for reference
                merged[addr]['old_name'] = old_name
        else:
            # Non-overlapping - add it
            merged[addr] = {
                'address': addr,
                'name': func.get('name', f'func_{addr:05x}'),
                'notes': func.get('notes', ''),
                'sig': func.get('sig', ''),
                'old_name': func.get('name', ''),  # Mark as from old registry
            }
            # Extract system from name if possible
            name_parts = merged[addr]['name'].split('_')
            if len(name_parts) > 0:
                merged[addr]['system'] = name_parts[0]
            added_count += 1
    
    print(f"  Added {added_count} non-overlapping functions from old registry")
    print(f"  Skipped {overlapping_count} overlapping functions (kept new names)")
    
    # Sort by address
    sorted_functions = sorted(merged.values(), key=lambda f: f['address'])
    
    print(f"\nTotal merged functions: {len(sorted_functions)}")
    
    # Write merged registry
    print(f"\nWriting merged registry to {merged_path}...")
    with open(merged_path, 'w') as f:
        f.write("# Falcon 3.0 Function Registry (MERGED)\n")
        f.write("# \n")
        f.write("# This is the SINGLE source of truth for all function names.\n")
        f.write("# Format: YAML for readability and tool compatibility\n")
        f.write("# \n")
        f.write(f"# MERGED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# - New registry: {len(new_functions)} functions (hand-curated, descriptive names)\n")
        f.write(f"# - Old registry: {added_count} non-overlapping functions added\n")
        f.write(f"# - Total: {len(sorted_functions)} functions\n")
        f.write("# \n")
        f.write("# Schema:\n")
        f.write("#   address: hex address (e.g., 0x11450)\n")
        f.write("#   name: descriptive function name (system_component_action_detail)\n")
        f.write("#   system: which system it belongs to\n")
        f.write("#   size: size in bytes (optional)\n")
        f.write("#   doc: description of what it does\n")
        f.write("#   source: where we learned about it (optional)\n")
        f.write("\n")
        f.write("schema: 1\n")
        f.write("\n")
        f.write("functions:\n")
        
        current_system = None
        for func in sorted_functions:
            system = func.get('system', 'unknown')
            
            # Add system header comments for readability
            if system != current_system:
                current_system = system
                f.write(f"\n  # {system.upper()} SYSTEM\n")
            
            f.write(format_function_yaml(func))
            f.write("\n")
    
    print(f"[OK] Merged registry saved to: {merged_path}")
    
    # Summary
    print("\n" + "="*80)
    print("MERGE SUMMARY")
    print("="*80)
    print(f"New registry functions: {len(new_functions)}")
    print(f"Old registry functions: {len(old_with_addresses)}")
    print(f"  - Overlapping: {overlapping_count} (kept new names)")
    print(f"  - Non-overlapping added: {added_count}")
    print(f"\nMerged registry total: {len(sorted_functions)}")
    print(f"\nNext steps:")
    print(f"  1. Review {merged_path}")
    print(f"  2. If satisfied: mv registry/functions_merged.yaml registry/functions.yaml")
    print(f"  3. Test with IDA: idat -A -S'apply_known_names.py' FALCONCD.EXE.i64")
    print(f"  4. Commit the merged registry")
    print("="*80)

if __name__ == "__main__":
    main()
