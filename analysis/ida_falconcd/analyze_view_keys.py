#!/usr/bin/env python3
"""
Analyze input_poll_handler for F2/F3/F4/F8 view key handling.
Scan codes: F2=0x3C, F3=0x3D, F4=0x3E, F8=0x42
"""

import json

# Load the detailed disassembly
with open('input_poll_handler_deepdive.json', 'r') as f:
    data = json.load(f)

instructions = data['instructions']
print(f"Total instructions in input_poll_handler: {len(instructions)}")
print(f"Function size: {data['size']} bytes")
print()

# Find the switch statement
print("="*80)
print("FINDING SWITCH STATEMENT")
print("="*80)

switch_start = None
for i, insn in enumerate(instructions):
    # Look for "sub bx, 0Fh; switch 67 cases"
    if 'switch' in insn.get('disasm', '').lower() and '67 cases' in insn.get('disasm', ''):
        switch_start = i
        print(f"Switch statement at index {i}, address 0x{insn['addr']:X}")
        print(f"  {insn['disasm']}")
        break

if not switch_start:
    print("ERROR: Could not find switch statement!")
    exit(1)

# Print context around switch
print("\nSwitch context:")
for i in range(max(0, switch_start-5), min(len(instructions), switch_start+10)):
    insn = instructions[i]
    marker = " >>> " if i == switch_start else "     "
    print(f"{marker}0x{insn['addr']:X}: {insn['disasm']}")

print()

# Find jump table reference
print("="*80)
print("SEARCHING FOR VIEW KEY CASES (scan codes 0x3C, 0x3D, 0x3E, 0x42)")
print("="*80)

# The switch subtracts 0xF from the scan code, so:
# F2 (0x3C) → case 0x3C - 0xF = 0x2D (45)
# F3 (0x3D) → case 0x3D - 0xF = 0x2E (46)
# F4 (0x3E) → case 0x3E - 0xF = 0x2F (47)
# F8 (0x42) → case 0x42 - 0xF = 0x33 (51)

view_cases = {
    0x2D: "F2",
    0x2E: "F3",
    0x2F: "F4",
    0x33: "F8"
}

# Look for case labels or comments mentioning these values
print("\nSearching for case values 0x2D, 0x2E, 0x2F, 0x33...")

# Also search for the original scan codes
scan_codes = [0x3C, 0x3D, 0x3E, 0x42]
print("\nSearching for scan code references (0x3C, 0x3D, 0x3E, 0x42)...")

found_refs = []
for i, insn in enumerate(instructions):
    disasm = insn.get('disasm', '')
    addr = insn['addr']
    
    # Check for scan codes or case values in operands
    for sc in scan_codes:
        if f'{sc:X}h' in disasm or f'0x{sc:X}' in disasm:
            found_refs.append((i, addr, sc, disasm))
    
    for case_val in view_cases.keys():
        if f'{case_val:X}h' in disasm or f'0x{case_val:X}' in disasm:
            found_refs.append((i, addr, case_val, disasm))

if found_refs:
    print(f"\nFound {len(found_refs)} potential references:")
    for idx, addr, val, disasm in found_refs[:20]:  # Limit output
        print(f"  0x{addr:X}: {disasm}")
        # Print context
        for j in range(max(0, idx-2), min(len(instructions), idx+3)):
            if j != idx:
                print(f"         0x{instructions[j]['addr']:X}: {instructions[j]['disasm']}")
        print()
else:
    print("No direct scan code references found in disassembly")

print()

# Look for function calls that might handle view switching
print("="*80)
print("FUNCTION CALLS IN input_poll_handler")
print("="*80)

calls = []
for insn in instructions:
    if insn['mnem'] == 'call':
        callee = insn.get('callee', 'unknown')
        addr = insn['addr']
        calls.append((addr, callee, insn['disasm']))

print(f"\nTotal function calls: {len(calls)}")
print("\nView-related calls:")
view_calls = [(a, c, d) for a, c, d in calls if any(kw in c.lower() for kw in ['view', 'camera', 'external', 'cockpit'])]
if view_calls:
    for addr, callee, disasm in view_calls:
        print(f"  0x{addr:X}: {callee}")
else:
    print("  (none found)")

print("\nAll unique callees (first 30):")
unique_callees = sorted(set(c for _, c, _ in calls))
for callee in unique_callees[:30]:
    count = len([c for _, c, _ in calls if c == callee])
    print(f"  {callee} ({count}x)")

# Save analysis
results = {
    'switch_found': switch_start is not None,
    'switch_location': instructions[switch_start]['addr'] if switch_start else None,
    'view_key_scan_codes': {
        'F2': '0x3C',
        'F3': '0x3D',
        'F4': '0x3E',
        'F8': '0x42'
    },
    'view_key_case_values': {k: f'0x{k:X}' for k in view_cases.keys()},
    'scan_code_refs': [{'addr': f'0x{a:X}', 'value': f'0x{v:X}', 'disasm': d} for _, a, v, d in found_refs],
    'total_calls': len(calls),
    'view_related_calls': [{'addr': f'0x{a:X}', 'callee': c} for a, c, _ in view_calls],
    'all_callees': unique_callees
}

with open('view_keys_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "="*80)
print(f"Analysis saved to view_keys_analysis.json")
