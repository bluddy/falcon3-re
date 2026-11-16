import json

with open('r57_loadout_menu_complete.json', 'r') as f:
    data = json.load(f)

sm = data['r57_menu_state_machine']

print("="*80)
print("FINDING STATE MACHINE MAIN LOOP")
print("="*80)

# Look for the main loop - likely has a jump back and tests against input
print("\nSearching for loop structures (jmp backwards)...")

for i, line in enumerate(sm['disassembly']):
    # Look for backward jumps (main loop indicator)
    if 'jmp' in line.lower() and 'loc_' in line:
        # Extract target
        parts = line.split('loc_')
        if len(parts) > 1:
            target = parts[1].split()[0]
            print(f"\nLine {i}: {line.strip()}")
            print(f"  Jump target: loc_{target}")
            
            # Show context around this jump
            print(f"\n  Context (10 lines before):")
            for j in range(max(0, i-10), i):
                print(f"    {j:3d}: {sm['disassembly'][j].strip()}")

# Look for calls to menu_r57_flight_display_handler to find state cases
print("\n" + "="*80)
print("CALLS TO menu_r57_flight_display_handler:")
print("="*80)

for i, line in enumerate(sm['disassembly']):
    if 'menu_r57_flight_display_handler' in line:
        print(f"\nLine {i}: {line.strip()}")
        # Show 15 lines before for context (should show the state check)
        print("  Context (15 lines before):")
        for j in range(max(0, i-15), i):
            print(f"    {j:3d}: {sm['disassembly'][j].strip()}")

# Look for comparison with immediate values (state checks)
print("\n" + "="*80)
print("STATE COMPARISONS (cmp with immediate):")
print("="*80)

state_checks = []
for i, line in enumerate(sm['disassembly']):
    if 'cmp' in line.lower() and (', 0' in line or ', 1' in line or ', 2' in line or ', 3' in line or ', 4' in line or ', 5' in line):
        state_checks.append((i, line))

print(f"\nFound {len(state_checks)} potential state checks:")
for i, (line_num, line) in enumerate(state_checks[:20]):  # First 20
    print(f"{line_num:3d}: {line.strip()}")
    # Show next 2 lines (likely jz/jnz)
    for j in range(line_num+1, min(line_num+3, len(sm['disassembly']))):
        print(f"     -> {sm['disassembly'][j].strip()}")
