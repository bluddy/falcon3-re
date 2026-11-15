#!/usr/bin/env python3
"""
Find handlers for number keys 0-9 (scan codes 0x02-0x0B) in input_poll_handler.
These handle view switching!
"""

import json

# Load input_poll_handler disassembly
with open('input_poll_handler_deepdive.json', 'r') as f:
    data = json.load(f)

instructions = data['instructions']

print("="*80)
print("SEARCHING FOR NUMBER KEY HANDLERS (scan codes 0x02-0x0B)")
print("="*80)
print()

# The switch at 0x12FDA9 subtracts 0x0F
# Number keys 0x02-0x0B are BEFORE this, so there must be earlier handling

print("First 100 instructions of input_poll_handler:")
print("(Looking for early exits, jumps, or dispatch before main switch)")
print()

for i in range(min(100, len(instructions))):
    insn = instructions[i]
    addr = insn['addr']
    disasm = insn['disasm']
    
    # Look for comparisons with small numbers (0x02-0x0B range)
    if 'cmp' in disasm.lower():
        print(f"{i:3d}. 0x{addr:X}: {disasm}")
    
    # Look for calls (might dispatch to view handlers)
    if 'call' in disasm.lower():
        print(f"{i:3d}. 0x{addr:X}: {disasm}  <-- CALL")
    
    # Look for jumps based on scan code
    if insn['mnem'] in ['jz', 'jnz', 'jbe', 'jb', 'ja', 'jae', 'je', 'jne']:
        print(f"{i:3d}. 0x{addr:X}: {disasm}  <-- BRANCH")

print()
print("="*80)
print("Looking for the scan code variable (var_6 from switch analysis)")
print("="*80)
print()

# From view_keys_analysis, we know var_6 holds the scan code
# Look for where it's set and used
for i in range(min(250, len(instructions))):
    insn = instructions[i]
    addr = insn['addr']
    disasm = insn['disasm']
    
    if 'var_6' in disasm or '[bp+' in disasm and '-6]' in disasm or '[bp-6]' in disasm:
        print(f"{i:3d}. 0x{addr:X}: {disasm}")

print()
print("Done. Check output for early handling before switch statement.")
