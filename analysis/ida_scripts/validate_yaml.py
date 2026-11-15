#!/usr/bin/env python3
"""
Validate and repair functions.yaml
"""
import re

def validate_yaml():
    """Read and report YAML issues"""
    with open('../../registry/functions.yaml', 'r') as f:
        lines = f.readlines()
    
    print(f"Total lines: {len(lines)}")
    print("\nChecking for issues...")
    
    issues = []
    in_doc = False
    doc_start = 0
    
    for i, line in enumerate(lines, 1):
        # Check for unterminated strings in doc: lines
        if 'doc:' in line:
            # Count quotes
            quotes = line.count("'")
            if quotes % 2 != 0:  # Odd number of quotes
                issues.append(f"Line {i}: Unterminated string in doc: {line.strip()[:80]}")
        
        # Check for ellipsis that might break YAML
        if '...' in line and 'doc:' in line:
            if not line.strip().endswith("'"):
                issues.append(f"Line {i}: Ellipsis without closing quote: {line.strip()[:80]}")
    
    if issues:
        print(f"\n{len(issues)} issues found:")
        for issue in issues[:20]:  # Show first 20
            print(f"  {issue}")
    else:
        print("No obvious issues found!")
    
    # Try to find the specific problematic line
    print("\n=== Lines 25-35 ===")
    for i in range(24, min(35, len(lines))):
        print(f"{i+1:4d}: {lines[i]}", end='')

if __name__ == '__main__':
    validate_yaml()
