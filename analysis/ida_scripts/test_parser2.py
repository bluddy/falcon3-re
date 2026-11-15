#!/usr/bin/env python3
"""Test the simple YAML parser"""

def parse_simple_yaml(yaml_path):
    """
    Simple YAML parser for our function registry format.
    Doesn't need full YAML spec - just handles our specific structure.
    """
    with open(yaml_path, 'r') as f:
        lines = f.readlines()
    
    functions = []
    current_func = {}
    
    for line in lines:
        line = line.rstrip('\n\r')
        
        # Skip comments and empty lines
        if not line or line.strip().startswith('#'):
            continue
        
        # New function entry (starts with "  - address:")
        if line.startswith('  - address:'):
            # Save previous function
            if current_func:
                functions.append(current_func)
            current_func = {}
            
            # Parse address
            addr_str = line.split(':', 1)[1].strip()
            current_func['address'] = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str)
        
        # Parse other fields
        elif line.startswith('    ') and ':' in line:
            key, value = line.strip().split(':', 1)
            value = value.strip()
            
            if key == 'size':
                current_func[key] = int(value)
            else:
                current_func[key] = value
    
    # Add last function
    if current_func:
        functions.append(current_func)
    
    return {'functions': functions}

data = parse_simple_yaml('../../registry/functions.yaml')
print(f"Parsed {len(data['functions'])} functions")
print("\nFirst 5:")
for f in data['functions'][:5]:
    print(f"  {hex(f['address'])}: {f['name']}")
print("\nLast 5:")
for f in data['functions'][-5:]:
    print(f"  {hex(f['address'])}: {f['name']}")
