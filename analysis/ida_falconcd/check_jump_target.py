#!/usr/bin/env python3
"""
Check what's at 0x13077C - the big jump target that might handle number keys.
"""

import json

with open('input_poll_handler_deepdive.json', 'r') as f:
    data = json.load(f)

instructions = data['instructions']
target_addr = 0x13077C

# Find the instruction at this address
target_idx = None
for i, insn in enumerate(instructions):
    if insn['addr'] == target_addr:
        target_idx = i
        break

if target_idx is None:
    print(f"ERROR: Address 0x{target_addr:X} not found in input_poll_handler!")
    print("This might be OUTSIDE the function - a far jump to another handler!")
    exit(1)

print("="*80)
print(f"CODE AT JUMP TARGET 0x{target_addr:X} (instruction {target_idx})")
print("="*80)
print()

# Print context around the jump target
context_size = 50

print(f"Context ({context_size} instructions before and after):")
print()

for i in range(max(0, target_idx - context_size), min(len(instructions), target_idx + context_size + 1)):
    insn = instructions[i]
    addr = insn['addr']
    disasm = insn['disasm']
    
    marker = " <-- JUMP TARGET" if i == target_idx else ""
    
    # Highlight key instructions
    if any(kw in insn['mnem'].lower() for kw in ['call', 'jmp', 'ret', 'cmp']):
        important = " ***"
    else:
        important = ""
    
    print(f"{i:4d}. 0x{addr:X}: {disasm}{marker}{important}")

print()
print("="*80)
print("LOOKING FOR NUMBER KEY HANDLING")
print("="*80)
print("Scan codes: 1=0x02, 2=0x03, ..., 9=0x0A, 0=0x0B")
print("Watch for comparisons with these values or dispatch tables!")
