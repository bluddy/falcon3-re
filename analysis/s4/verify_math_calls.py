"""
Verify the math function calls from view_projection.

Check if the call targets actually exist in the parent functions.
"""

import json

# Load data
with open('segment_map.json') as f:
    seg_map = json.load(f)

with open('../ida_falconcd/function_bytes.json') as f:
    func_bytes = json.load(f)

# Call targets from view_projection
calls = [
    {'addr': 0x1CC57, 'segoff': 'seg015:0C65', 'parent': 'stream_command_interpret', 'offset': 0x002A},
    {'addr': 0x1CC6C, 'segoff': 'seg015:0C7A', 'parent': 'stream_command_interpret', 'offset': 0x003F},
    {'addr': 0x1CCCD, 'segoff': 'seg015:0CDB', 'parent': 'stream_command_interpret', 'offset': 0x00A0},
    {'addr': 0x1CCE2, 'segoff': 'seg015:0CF0', 'parent': 'stream_command_interpret', 'offset': 0x00B5},
    {'addr': 0x1CD43, 'segoff': 'seg015:0D51', 'parent': 'stream_command_interpret', 'offset': 0x0116},
    {'addr': 0x1CD58, 'segoff': 'seg015:0D66', 'parent': 'stream_command_interpret', 'offset': 0x012B},
    {'addr': 0x1D8B2, 'segoff': 'seg017:021C', 'parent': 'group_children_release', 'offset': 0x0026},
    {'addr': 0x1D879, 'segoff': 'seg017:01E3', 'parent': 'channel_list_register_batch', 'offset': 0x009F},
    {'addr': 0x1D894, 'segoff': 'seg017:01FE', 'parent': 'group_children_release', 'offset': 0x0008},
    {'addr': 0x210EF, 'segoff': 'seg020:1A2F', 'parent': 'vec_delta_norm_1f6ee', 'offset': 0x00E0},
]

print("=" * 70)
print("Verifying view_projection Call Targets")
print("=" * 70)

# Get parent function info
parents = {}
for call in calls:
    parent_name = call['parent']
    if parent_name not in parents:
        # Find in segment_map
        for func in seg_map['functions']:
            if func['name'] == parent_name:
                parents[parent_name] = {
                    'start_ea': func['start_ea'],
                    'end_ea': func['end_ea'],
                    'size': func['end_ea'] - func['start_ea'],
                    'segoff': func['segoff']
                }
                break

print("\nParent Functions:")
print("-" * 70)
for name, info in parents.items():
    print(f"{name}:")
    print(f"  {info['segoff']}, 0x{info['start_ea']:05X}-0x{info['end_ea']:05X}, {info['size']} bytes")

print("\n" + "=" * 70)
print("Call Target Verification")
print("=" * 70)

for call in calls:
    parent = parents[call['parent']]
    addr = call['addr']
    
    # Verify address is within parent function
    within = parent['start_ea'] <= addr < parent['end_ea']
    calc_offset = addr - parent['start_ea']
    
    print(f"\n{call['segoff']} (0x{addr:05X}):")
    print(f"  Parent: {call['parent']}")
    print(f"  Expected offset: +0x{call['offset']:04X}")
    print(f"  Actual offset:   +0x{calc_offset:04X}")
    print(f"  Within bounds: {within}")
    
    if not within:
        print(f"  ERROR: Address is OUTSIDE parent function!")
        print(f"    Parent range: 0x{parent['start_ea']:05X}-0x{parent['end_ea']:05X}")
    
    if calc_offset != call['offset']:
        print(f"  WARNING: Offset mismatch!")

# Check multi-entry points
print("\n" + "=" * 70)
print("Multi-Entry Point Matches")
print("=" * 70)

for call in calls:
    parent_name = call['parent']
    addr = call['addr']
    
    # Check if this address is listed as a multi-entry point
    multi_entries = seg_map['multi_entry_functions'].get(parent_name, [])
    
    found = False
    for entry in multi_entries:
        if entry['address'] == addr:
            print(f"\n[OK] {call['segoff']} IS a registered multi-entry point")
            print(f"  XRefs: {entry['xref_count']}")
            found = True
            break
    
    if not found:
        print(f"\n[NO] {call['segoff']} is NOT a registered multi-entry point")
        print(f"  This address is called by view_projection but not detected by export")
        print(f"  Possible reasons:")
        print(f"    - Export script missed it")
        print(f"    - view_projection is the ONLY caller")
        print(f"    - It's a fall-through address, not a jump target")

print("\n" + "=" * 70)
print("Conclusion")
print("=" * 70)

unregistered = sum(1 for c in calls if c['addr'] not in 
                   [e['address'] for entries in seg_map['multi_entry_functions'].values() 
                    for e in entries])

print(f"""
Total call targets: {len(calls)}
Unregistered multi-entries: {unregistered}

This suggests:
1. view_projection has exclusive access to some code paths
2. These functions may be specifically designed as math libraries
3. The functions may have multiple "entry points" that are sequential
   rather than branched-to

Next: Check if these are actually DISTINCT functions that happen to be
      adjacent in memory, or true multi-entry shared code.
""")
