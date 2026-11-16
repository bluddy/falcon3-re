"""
Find the input dispatcher that processes input_flag_pending_2.

The dispatcher should:
1. Read input_flag_pending_2 into a register (ax/bx/cx/dx)
2. Use that value to branch (cmp/jmp/switch table)
3. Call different handlers based on scan code

Focus on the functions that READ the flag.
"""

import json

# Load the input_flag_refs.json
with open(r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\input_flag_refs.json", 'r') as f:
    data = json.load(f)

print("=" * 80)
print("FINDING INPUT DISPATCHER")
print("=" * 80)
print()

# Find all MOV reads (loads value into register)
reads = []
for ref in data['references']:
    insn = ref['insn']
    # Look for "mov <reg>, es:input_flag_pending_2"
    if insn.startswith('mov     ax, es:input_flag_pending_2'):
        reads.append(ref)

print(f"Found {len(reads)} functions that load input_flag_pending_2 into AX:")
print()

# Group by segment to understand overlay structure
by_segment = {}
for ref in reads:
    seg = ref['segment']
    if seg not in by_segment:
        by_segment[seg] = []
    by_segment[seg].append(ref)

for seg in sorted(by_segment.keys()):
    refs = by_segment[seg]
    print(f"{seg}: {len(refs)} read(s)")
    for ref in refs:
        print(f"  0x{ref['addr']} in {ref['func']}")

print()
print("=" * 80)
print("ANALYSIS STRATEGY")
print("=" * 80)
print()
print("The dispatcher is likely in one of these overlays (game mode handlers):")
print()

# Prioritize game mode coordinators
priority_funcs = [
    ('r29_tactical_screen_coordinator', 'R29_2F8As'),
    ('game_mode_r53_main_coordinator', 'R53_569Fs'),
]

print("Top priority candidates:")
for ref in reads:
    if any(ref['func'] == name for name, _ in priority_funcs):
        print(f"  {ref['func']} at {ref['addr']} in {ref['segment']}")

print()
print("Next steps:")
print("1. For each READ, check if followed by:")
print("   - sub ax, 2 (normalize scan code 0x02-0x0B to 0x00-0x09)")
print("   - cmp ax, <value> / jz <handler>")
print("   - jmp [table + ax*2] (jump table)")
print("   - call [table + ax*2] (call table)")
print()
print("2. Look for switch statement patterns:")
print("   - Multiple sequential cmp/jz pairs")
print("   - Bounds check (cmp ax, 10)")
print("   - Indexed jumps")
print()
print("3. The dispatcher might:")
print("   - Call different view functions directly")
print("   - Set r15_external_view_flag based on which view type")
print("   - Pass scan code as parameter to a generic handler")
