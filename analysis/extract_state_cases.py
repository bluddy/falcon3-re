import json

with open('r57_loadout_menu_complete.json', 'r') as f:
    data = json.load(f)

sm = data['r57_menu_state_machine']

print("="*80)
print("STATE MACHINE CASE STRUCTURE")
print("="*80)

# The switch is at line 161, cases start at 162
# Find all "Case N:" comments
cases = []
for i, line in enumerate(sm['disassembly']):
    if '; Case' in line or 'case ' in line.lower():
        cases.append(i)
        
print(f"\nFound {len(cases)} state cases:\n")

# Show each case with context
for case_idx, start_line in enumerate(cases):
    # Find end of this case (next case or end of function)
    if case_idx + 1 < len(cases):
        end_line = cases[case_idx + 1]
    else:
        end_line = min(start_line + 50, len(sm['disassembly']))
    
    print(f"\n{'='*80}")
    print(f"STATE CASE starting at line {start_line}:")
    print('='*80)
    
    # Show this case
    for i in range(start_line, min(end_line, start_line + 40)):
        line = sm['disassembly'][i]
        # Highlight important lines
        marker = ""
        if 'call' in line and 'menu_r57' in line:
            marker = " <-- DISPLAY HANDLER"
        elif 'call' in line and 'overlay_' in line:
            marker = " <-- OVERLAY"
        elif 'mov' in line and 'current_view_index' in line:
            marker = " <-- STATE CHANGE"
        elif 'jmp' in line and 'loc_' in line:
            marker = " <-- JUMP"
            
        print(f"{i:3d}: {line.rstrip()}{marker}")

# Show the full range from line 160 to 200 to understand flow
print("\n\n" + "="*80)
print("DETAILED VIEW: Lines 160-200 (Core state machine)")
print("="*80)
for i in range(160, min(200, len(sm['disassembly']))):
    print(f"{i:3d}: {sm['disassembly'][i]}")
