#!/usr/bin/env python3
"""
Extract terrain seed functions using regex (YAML-independent)
"""
import re
import json

def extract_terrain_functions():
    """Extract terrain functions without parsing YAML"""
    with open('../../registry/functions.yaml', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match function entries with system: terrain
    # Match: address, name, system: terrain
    pattern = r'-\s+address:\s+(0x[0-9a-fA-F]+)\s+name:\s+([^\n]+)\s+system:\s+terrain'
    
    matches = re.findall(pattern, content)
    
    seeds = {}
    for addr, name in matches:
        seeds[name.strip()] = addr
    
    print(f"Found {len(seeds)} terrain functions")
    
    # Write seeds file
    with open('../terrain_seeds.json', 'w') as f:
        json.dump(seeds, f, indent=2)
    
    print(f"Wrote terrain_seeds.json")
    
    # Show first 10
    print("\nFirst 10 terrain seeds:")
    for i, (name, addr) in enumerate(list(seeds.items())[:10]):
        print(f"  {addr}: {name}")
    
    return seeds

if __name__ == '__main__':
    seeds = extract_terrain_functions()
