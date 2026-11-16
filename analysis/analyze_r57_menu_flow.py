import json
from collections import defaultdict

# Load the R57 extraction
with open('r57_loadout_menu_complete.json', 'r') as f:
    r57_data = json.load(f)

print("="*80)
print("R57 LOADOUT MENU - FLOW ANALYSIS")
print("="*80)

# Build call graph
call_graph = defaultdict(list)
called_by_graph = defaultdict(list)

for func_name, func_data in r57_data.items():
    for call in func_data['calls']:
        call_graph[func_name].append(call['name'])
        called_by_graph[call['name']].append(func_name)

# Find entry points (functions called from outside R57)
print("\n1. ENTRY POINTS (called from outside R57):")
print("-" * 80)
for func_name in sorted(r57_data.keys()):
    external_callers = [c for c in r57_data[func_name]['called_by'] 
                       if not any(c['name'] in r57_data for c in r57_data[func_name]['called_by'])]
    if external_callers or not r57_data[func_name]['called_by']:
        size = r57_data[func_name]['size']
        num_calls = len(r57_data[func_name]['calls'])
        print(f"\n  {func_name} ({size}B, {num_calls} calls)")
        if external_callers:
            for caller in external_callers[:5]:  # Show first 5
                print(f"    <- {caller['name']}")
        else:
            print(f"    (No callers found - may be overlay entry point)")

# Show call hierarchy
print("\n\n2. CALL HIERARCHY:")
print("-" * 80)

def print_call_tree(func_name, indent=0, visited=None):
    if visited is None:
        visited = set()
    if func_name in visited:
        print("  " * indent + f"-> {func_name} (circular)")
        return
    visited.add(func_name)
    
    if func_name not in r57_data:
        print("  " * indent + f"-> {func_name} (external)")
        return
    
    func_data = r57_data[func_name]
    size = func_data['size']
    calls = func_data['calls']
    
    print("  " * indent + f"-> {func_name} ({size}B, {len(calls)} calls)")
    
    # Only show R57 calls
    r57_calls = [c for c in calls if c['name'] in r57_data]
    for call in r57_calls[:10]:  # Limit depth
        print_call_tree(call['name'], indent + 1, visited.copy())

# Start from likely entry points
entry_points = ['r57_menu_state_machine', 'r57_loadout_display_handler', 
                'overlay_r57_logic', 'overlay_r57_processor_2']

for entry in entry_points:
    if entry in r57_data:
        print(f"\nFrom {entry}:")
        print_call_tree(entry, 1)

# Show functions by size
print("\n\n3. FUNCTIONS BY SIZE:")
print("-" * 80)
for func_name in sorted(r57_data.keys(), key=lambda x: r57_data[x]['size'], reverse=True):
    size = r57_data[func_name]['size']
    calls = len(r57_data[func_name]['calls'])
    strings = len(r57_data[func_name]['strings'])
    print(f"  {func_name:45s} {size:5d}B  {calls:3d} calls  {strings:2d} strings")

# Show string references
print("\n\n4. STRING REFERENCES:")
print("-" * 80)
for func_name in sorted(r57_data.keys()):
    strings = r57_data[func_name]['strings']
    if strings:
        print(f"\n  {func_name}:")
        for s in strings[:10]:  # Show first 10
            print(f"    '{s['string']}'")

# Analyze state machine
print("\n\n5. STATE MACHINE ANALYSIS:")
print("-" * 80)
if 'r57_menu_state_machine' in r57_data:
    sm = r57_data['r57_menu_state_machine']
    print(f"\n  r57_menu_state_machine ({sm['size']}B)")
    print(f"  Calls {len(sm['calls'])} functions:")
    
    # Group calls by name
    call_counts = defaultdict(int)
    for call in sm['calls']:
        call_counts[call['name']] += 1
    
    for name, count in sorted(call_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {count:2d}x {name}")

print("\n" + "="*80)
