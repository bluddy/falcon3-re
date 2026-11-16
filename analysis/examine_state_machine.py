import json

with open('r57_loadout_menu_complete.json', 'r') as f:
    data = json.load(f)

sm = data['r57_menu_state_machine']

print("="*80)
print("R57 STATE MACHINE ANALYSIS")
print("="*80)
print(f"\nFunction: r57_menu_state_machine")
print(f"Address: {sm['address']}")
print(f"Size: {sm['size']} bytes")
print(f"Total instructions: {len(sm['disassembly'])}")
print(f"Total calls: {len(sm['calls'])}")

print("\n" + "="*80)
print("DISASSEMBLY - First 100 lines:")
print("="*80)

for i, line in enumerate(sm['disassembly'][:100]):
    print(f"{i:4d}: {line}")

print("\n" + "="*80)
print("KEY CALL SITES:")
print("="*80)

# Find calls to the display handlers
display_handler_calls = [c for c in sm['calls'] if 'display' in c['name'].lower() or 'r57' in c['name'].lower()]
print(f"\nFound {len(display_handler_calls)} calls to display/r57 functions:")
for call in display_handler_calls:
    print(f"  {call['address']}: {call['name']}")

# Find global variable references
print("\n" + "="*80)
print("GLOBAL VARIABLE REFERENCES:")
print("="*80)

# Look for references to key globals in disassembly
key_globals = [
    'menu_current_flight_index',
    'menu_total_flights_count', 
    'menu_loadout_mode_flag',
    'menu_loadout_data_ptr',
    'menu_flight_records_ptr'
]

for global_name in key_globals:
    count = sum(1 for line in sm['disassembly'] if global_name in line)
    if count > 0:
        print(f"{global_name}: {count} references")
        # Show first few references
        refs = [(i, line) for i, line in enumerate(sm['disassembly']) if global_name in line]
        for i, line in refs[:3]:
            print(f"  Line {i}: {line.strip()}")
