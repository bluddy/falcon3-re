import json

with open('r57_loadout_menu_complete.json', 'r') as f:
    data = json.load(f)

sm = data['r57_menu_state_machine']

print("="*80)
print("STATE MACHINE JUMP TABLE AREA")
print("="*80)

# Show lines 135-175 (around the jump table reference)
for i in range(135, min(175, len(sm['disassembly']))):
    line = sm['disassembly'][i]
    print(f"{i:3d}: {line}")

# Find all jumptable references
print("\n" + "="*80)
print("ALL JUMPTABLE REFERENCES:")
print("="*80)

for i, line in enumerate(sm['disassembly']):
    if 'jumptable' in line.lower():
        print(f"{i:3d}: {line.strip()}")
        # Show 5 lines before and after
        print("  Context:")
        for j in range(max(0, i-3), min(i+4, len(sm['disassembly']))):
            print(f"    {j:3d}: {sm['disassembly'][j].strip()}")
        print()
