#!/usr/bin/env python3
"""Update function registry with ranks 101-110 analysis"""

import sys

# Read the entire registry
registry_path = r'c:\Users\ybarnoy\projects\falcon3\registry\functions.yaml'

with open(registry_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Define updates
updates = {
    '0x11c884': ('utility_11c884', 'Utility function (24 calls) - needs further investigation'),
    '0x11c90f': ('utility_11c90f', 'Utility function (24 calls) - needs further investigation'),
    '0x13536f': ('vector_arithmetic_complex', 'Complex vector/coordinate arithmetic operations (1085B, 24 calls)'),
    '0x13bce5': ('string_cr_null_terminate', 'Append CR (0Dh) and null terminator to string'),
    '0x11c642': ('utility_11c642', 'Utility function (22 calls) - needs further investigation'),
}

# Process lines
output_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    output_lines.append(line)
    
    # Check if this is an address line we want to update
    for addr, (new_name, description) in updates.items():
        if f'address: {addr}' in line:
            # Next line should be name
            i += 1
            if i < len(lines) and 'name:' in lines[i]:
                old_name = lines[i].strip().split('name: ')[1]
                output_lines.append(f'    name: {new_name}\n')
                print(f"  Updated {addr}: {old_name} -> {new_name}")
                
                # Add/update description
                i += 1
                if i < len(lines):
                    # Check if next line is size or description
                    if 'size:' in lines[i]:
                        # Insert description before size
                        output_lines.append(f'    description: {description}\n')
                        output_lines.append(lines[i])
                        print(f"    Added description")
                    elif 'description:' in lines[i]:
                        # Replace existing description
                        output_lines.append(f'    description: {description}\n')
                        print(f"    Updated description")
                    else:
                        output_lines.append(lines[i])
            else:
                if i < len(lines):
                    output_lines.append(lines[i])
            break
    i += 1

# Write back
with open(registry_path, 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print("\n[+] Registry updated successfully!")
