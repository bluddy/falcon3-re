#!/usr/bin/env python3
"""
Rebuild a clean YAML from the broken one by fixing syntax issues on-the-fly.
"""
import re
from datetime import datetime

def rebuild_yaml():
    """Rebuild YAML with proper escaping and quoting."""
    
    with open('../../registry/functions.yaml', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Start with header
    output = []
    output.append(f"# Falcon 3.0 Function Registry\n")
    output.append(f"#\n")
    output.append(f"# REBUILT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    output.append(f"# Total functions: (calculated after rebuild)\n")
    output.append(f"#\n")
    output.append(f"# Schema:\n")
    output.append(f"#   address: hex address (e.g., 0x11450)\n")
    output.append(f"#   name: descriptive function name\n")
    output.append(f"#   system: which system it belongs to\n")
    output.append(f"#   size: size in bytes (optional)\n")
    output.append(f"#   doc: description (optional)\n")
    output.append(f"#   source: where we learned about it (optional)\n")
    output.append(f"\n")
    output.append(f"schema: 1\n")
    output.append(f"\n")
    output.append(f"functions:\n")
    
    current_function = None
    func_count = 0
    fixes = 0
    
    in_functions = False
    for i, line in enumerate(lines, 1):
        # Skip header until we hit "functions:"
        if not in_functions:
            if line.strip() == "functions:":
                in_functions = True
            continue
        
        # Process function entries
        stripped = line.strip()
        
        # Comment lines - pass through
        if stripped.startswith('#'):
            output.append(line)
            continue
        
        # Empty lines - pass through
        if not stripped:
            output.append('\n')
            continue
        
        # New function entry
        if stripped.startswith('- address:'):
            if current_function:
                # Write previous function
                output.extend(format_function(current_function))
                func_count += 1
            
            # Start new function
            addr_match = re.search(r'0x[0-9a-fA-F]+', stripped)
            if addr_match:
                current_function = {'address': addr_match.group(0)}
            continue
        
        # Function fields
        if current_function:
            if 'name:' in stripped:
                name_match = re.search(r'name:\s*(.+)', stripped)
                if name_match:
                    current_function['name'] = name_match.group(1).strip()
            
            elif 'system:' in stripped:
                system_match = re.search(r'system:\s*(.+)', stripped)
                if system_match:
                    current_function['system'] = system_match.group(1).strip()
            
            elif 'size:' in stripped:
                size_match = re.search(r'size:\s*(\d+)', stripped)
                if size_match:
                    current_function['size'] = int(size_match.group(1))
            
            elif 'doc:' in stripped:
                # Extract doc string, handle quotes
                doc_match = re.search(r"doc:\s*['\"]?(.+?)['\"]?\s*$", stripped)
                if doc_match:
                    doc = doc_match.group(1)
                    # Remove trailing quotes if present
                    doc = doc.strip("'\"")
                    current_function['doc'] = doc
            
            elif 'source:' in stripped:
                source_match = re.search(r'source:\s*(.+)', stripped)
                if source_match:
                    current_function['source'] = source_match.group(1).strip()
    
    # Write last function
    if current_function:
        output.extend(format_function(current_function))
        func_count += 1
    
    # Update count in header
    output[3] = f"# Total functions: {func_count}\n"
    
    # Write clean file
    with open('../../registry/functions_clean.yaml', 'w', encoding='utf-8') as f:
        f.writelines(output)
    
    print(f"Rebuilt YAML with {func_count} functions")
    print(f"Saved to: registry/functions_clean.yaml")
    
    # Validate
    print("\nValidating clean YAML...")
    try:
        import yaml
        with open('../../registry/functions_clean.yaml', 'r') as f:
            data = yaml.safe_load(f)
        print(f"[OK] Successfully parsed! Found {len(data['functions'])} functions")
        
        # Replace old with new
        print("\nReplacing old functions.yaml with clean version...")
        import shutil
        shutil.move('../../registry/functions.yaml', '../../registry/functions.yaml.backup')
        shutil.move('../../registry/functions_clean.yaml', '../../registry/functions.yaml')
        print("[OK] Replaced functions.yaml")
        
    except Exception as e:
        print(f"[ERROR] Validation failed: {e}")
        return False
    
    return True

def format_function(func):
    """Format a function entry with proper YAML syntax."""
    lines = []
    lines.append(f"  - address: {func['address']}\n")
    lines.append(f"    name: {func['name']}\n")
    
    if 'system' in func:
        lines.append(f"    system: {func['system']}\n")
    
    if 'size' in func:
        lines.append(f"    size: {func['size']}\n")
    
    if 'doc' in func:
        # Properly escape and quote doc strings
        doc = func['doc']
        # Escape single quotes
        doc = doc.replace("'", "''")
        # Use single quotes for the whole string
        lines.append(f"    doc: '{doc}'\n")
    
    if 'source' in func:
        # Quote source if it contains special characters
        source = func['source']
        if ':' in source or '(' in source or ')' in source:
            source = source.replace("'", "''")  # Escape quotes
            lines.append(f"    source: '{source}'\n")
        else:
            lines.append(f"    source: {source}\n")
    
    return lines

if __name__ == '__main__':
    rebuild_yaml()
