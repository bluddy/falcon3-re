#!/usr/bin/env python3
"""
Extract the code between var_6 being set and the switch statement.
This should contain number key (0-9) handlers for view switching.
"""

import json

with open('input_poll_handler_deepdive.json', 'r') as f:
    data = json.load(f)

instructions = data['instructions']

# Find where var_6 is set and where switch starts
var6_set_idx = None
switch_idx = None

for i, insn in enumerate(instructions):
    if 'mov' in insn['disasm'] and 'var_6' in insn['disasm'] and ', ax' in insn['disasm']:
        var6_set_idx = i
    if 'sub     bx, 0Fh; switch 67 cases' in insn['disasm']:
        switch_idx = i
        break

print("="*80)
print(f"CODE BETWEEN var_6 SET AND SWITCH STATEMENT")
print("="*80)
print(f"\nvar_6 set at instruction {var6_set_idx} (0x{instructions[var6_set_idx]['addr']:X})")
print(f"Switch starts at instruction {switch_idx} (0x{instructions[switch_idx]['addr']:X})")
print(f"\n{switch_idx - var6_set_idx} instructions between them")
print()

# Print all instructions between
print("Full disassembly:")
print()

for i in range(var6_set_idx, switch_idx + 3):
    insn = instructions[i]
    addr = insn['addr']
    disasm = insn['disasm']
    
    marker = ""
    if i == var6_set_idx:
        marker = " <-- var_6 SET"
    elif i == switch_idx:
        marker = " <-- SWITCH START"
    
    # Highlight important instructions
    if any(kw in insn['mnem'].lower() for kw in ['call', 'jmp', 'jz', 'jnz', 'cmp']):
        marker2 = " ***"
    else:
        marker2 = ""
    
    print(f"{i:3d}. 0x{addr:X}: {disasm}{marker}{marker2}")

print()
print("="*80)
print("ANALYSIS:")
print("If number keys (0x02-0x0B) are handled here, we should see:")
print("- Comparisons with small values (< 0x0F)")
print("- Conditional jumps/calls based on scan code")
print("- Possibly a lookup table or early dispatch")
print("="*80)
