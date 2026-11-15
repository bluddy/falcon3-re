#!/usr/bin/env python3
"""
Repair functions.yaml by closing unterminated doc strings
"""
import re

def repair_yaml():
    """Fix unterminated strings in doc: lines"""
    with open('../../registry/functions.yaml', 'r') as f:
        lines = f.readlines()
    
    fixed = 0
    for i, line in enumerate(lines):
        # Look for lines with doc: that have an odd number of quotes
        if '    doc:' in line or '    doc :' in line:
            quotes = line.count("'")
            if quotes % 2 != 0:  # Odd number - needs closing quote
                # Add closing quote before newline
                lines[i] = line.rstrip() + "'\n"
                fixed += 1
    
    # Write repaired file
    with open('../../registry/functions.yaml', 'w') as f:
        f.writelines(lines)
    
    print(f"Fixed {fixed} unterminated doc strings")
    
    # Try to parse it
    print("\nValidating repaired YAML...")
    try:
        import yaml
        with open('../../registry/functions.yaml', 'r') as f:
            data = yaml.safe_load(f)
        print(f"✓ Successfully parsed! Found {len(data['functions'])} functions")
        return True
    except Exception as e:
        print(f"✗ Still has errors: {e}")
        return False

if __name__ == '__main__':
    repair_yaml()
