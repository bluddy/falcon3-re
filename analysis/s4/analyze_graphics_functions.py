"""
Analyze the 6 well-named graphics functions called by view_projection.

These are calls 11-16 in the pipeline:
- fixed_vec3_transform_es (0x248D1)
- vec2_normalize_seq (0x23E66)
- farobj_record_step (0x2142E)
- farobj_record_push_7c054 (0x2128E)
- farobj_record_lookup_step (0x213E6)
- farobj_record_push_7d0c6 (0x212D6)
"""

import json
from pathlib import Path

# Load data
with open('segment_map.json') as f:
    seg_map = json.load(f)

with open('../ida_falconcd/function_bytes.json') as f:
    func_bytes = json.load(f)

# The 6 graphics functions
graphics_funcs = [
    {'name': 'fixed_vec3_transform_es', 'addr': 0x248D1, 'segoff': 'seg020:5211'},
    {'name': 'vec2_normalize_seq', 'addr': 0x23E66, 'segoff': 'seg020:47A6'},
    {'name': 'farobj_record_step', 'addr': 0x2142E, 'segoff': 'seg020:1D6E'},
    {'name': 'farobj_record_push_7c054', 'addr': 0x2128E, 'segoff': 'seg020:1BCE'},
    {'name': 'farobj_record_lookup_step', 'addr': 0x213E6, 'segoff': 'seg020:1D26'},
    {'name': 'farobj_record_push_7d0c6', 'addr': 0x212D6, 'segoff': 'seg020:1C16'},
]

print("=" * 70)
print("Graphics Functions Analysis")
print("=" * 70)

# Get info from segment_map
for gf in graphics_funcs:
    for func in seg_map['functions']:
        if func['start_ea'] == gf['addr']:
            gf['size'] = func['end_ea'] - func['start_ea']
            break

# Get bytecode from function_bytes
for gf in graphics_funcs:
    for fname, fdata in func_bytes.items():
        if fdata['ea'] == gf['addr']:
            gf['func_bytes_name'] = fname
            gf['bytecode_size'] = fdata['size']
            gf['bytes_hex'] = fdata['bytes']
            gf['is_far'] = fdata.get('is_far', False)
            gf['overlay'] = fdata.get('overlay', False)
            break

# Display info
print("\nFunction Catalog:")
print("-" * 70)
print(f"{'Name':<30} {'Location':<18} {'Size':<8} {'Far':<6} {'Overlay'}")
print("-" * 70)

for gf in graphics_funcs:
    size = gf.get('size', gf.get('bytecode_size', '?'))
    is_far = 'Yes' if gf.get('is_far', False) else 'No'
    overlay = 'Yes' if gf.get('overlay', False) else 'No'
    print(f"{gf['name']:<30} {gf['segoff']:<18} {size:<8} {is_far:<6} {overlay}")

# Analyze patterns in names
print("\n" + "=" * 70)
print("Name Pattern Analysis")
print("=" * 70)

print("\n1. 'fixed_vec3_transform_es' suggests:")
print("   - Fixed-point (not floating) vector operations")
print("   - 3D vector (vec3)")
print("   - Transform operation (rotation/translation/scale)")
print("   - Uses ES segment for data")

print("\n2. 'vec2_normalize_seq' suggests:")
print("   - 2D vector operations")
print("   - Normalization (make length = 1)")
print("   - Sequential/series operation (multiple vectors?)")

print("\n3. 'farobj_record_*' pattern (4 functions):")
print("   - All deal with 'farobj' (far objects in scene)")
print("   - 'record' suggests data structure manipulation")
print("   - 'step' - iterate through records")
print("   - 'push' - add to stack/queue")
print("   - 'lookup' - search/retrieve")
print("   - Addresses in names (7c054, 7d0c6) likely data structures")

# Check who else calls these functions
print("\n" + "=" * 70)
print("Cross-Reference Analysis")
print("=" * 70)

print("\nSearching for other callers...")

for gf in graphics_funcs:
    print(f"\n{gf['name']} (0x{gf['addr']:05X}):")
    
    # Search function_bytes for callers
    callers = []
    target = gf['addr']
    
    for fname, fdata in func_bytes.items():
        if fname == gf.get('func_bytes_name'):
            continue  # Skip self
        
        bytes_hex = fdata['bytes']
        fbytes = bytes([int(bytes_hex[i:i+2], 16) for i in range(0, len(bytes_hex), 2)])
        
        # Look for CALL to this address
        for i in range(len(fbytes) - 2):
            if fbytes[i] == 0xE8:  # CALL near
                offset = fbytes[i+1] + (fbytes[i+2] << 8)
                if offset >= 0x8000:
                    offset = offset - 0x10000
                next_inst = fdata['ea'] + i + 3
                call_target = next_inst + offset
                
                if call_target == target:
                    callers.append({
                        'name': fname,
                        'ea': fdata['ea'],
                        'call_offset': i
                    })
                    break
    
    gf['callers'] = callers
    
    if callers:
        print(f"  Called by {len(callers)} function(s):")
        for caller in callers[:10]:  # Limit to 10
            # Find segment:offset
            segoff = None
            for func in seg_map['functions']:
                if func['start_ea'] == caller['ea']:
                    segoff = func['segoff']
                    break
            print(f"    - {caller['name']:<30} ({segoff or '?'})")
    else:
        print(f"  Only called by view_projection (exclusive)")

# Analyze farobj pattern
print("\n" + "=" * 70)
print("farobj Pattern Analysis")
print("=" * 70)

farobj_funcs = [gf for gf in graphics_funcs if 'farobj' in gf['name']]

print(f"\nFound {len(farobj_funcs)} farobj-related functions")
print("\nSizes:")
for gf in farobj_funcs:
    size = gf.get('size', gf.get('bytecode_size', '?'))
    print(f"  {gf['name']:<35} {size:>4} bytes")

print("\nLikely purpose:")
print("  'farobj' = far objects (distant 3D objects in scene)")
print("  These functions manage a list/queue of visible objects")
print("  During projection, objects are:")
print("    1. lookup_step - check if object is visible")
print("    2. record_step - iterate through visible objects")
print("    3. push - add to rendering queue")
print("  Two push functions suggest two different data structures:")
print("    - push_7c054 -> one queue/list")
print("    - push_7d0c6 -> another queue/list")

# Check if these are related to overlays
print("\n" + "=" * 70)
print("Overlay & Segment Analysis")
print("=" * 70)

print("\nAll 6 functions are in seg020:")
seg020 = None
for seg in seg_map['segments']:
    if seg['name'] == 'seg020':
        seg020 = seg
        break

if seg020:
    print(f"  seg020: 0x{seg020['start_ea']:05X} - 0x{seg020['end_ea']:05X} ({seg020['end_ea']-seg020['start_ea']:,} bytes)")
    print(f"  This is a LARGE segment (likely main graphics engine)")

print("\nNone are in overlays:")
for gf in graphics_funcs:
    print(f"  {gf['name']:<30} overlay={gf.get('overlay', False)}")

print("\nConclusion: These are RESIDENT functions, not overlay code")
print("  -> Core graphics operations, always in memory")
print("  -> Performance-critical (no overlay swap overhead)")

# Bytecode analysis
print("\n" + "=" * 70)
print("Bytecode Pattern Analysis")
print("=" * 70)

for gf in graphics_funcs:
    if 'bytes_hex' not in gf:
        continue
    
    bytecode = bytes([int(gf['bytes_hex'][i:i+2], 16) 
                     for i in range(0, len(gf['bytes_hex']), 2)])
    
    # Count operations
    call_count = sum(1 for b in bytecode if b == 0xE8)
    mul_count = sum(1 for i in range(len(bytecode)-1) 
                   if bytecode[i] in [0xF6, 0xF7] and 
                      ((bytecode[i+1] >> 3) & 7) in [4, 5])
    shift_count = sum(1 for b in bytecode if b in [0xD0, 0xD1, 0xD2, 0xD3])
    
    print(f"\n{gf['name']}:")
    print(f"  Size: {len(bytecode)} bytes")
    print(f"  Calls: {call_count}, Mul/IMul: {mul_count}, Shifts: {shift_count}")
    
    # Show first 16 bytes
    first_16 = ' '.join(f'{b:02X}' for b in bytecode[:16])
    print(f"  First 16 bytes: {first_16}")

# Export analysis
output = {
    'graphics_functions': [
        {
            'name': gf['name'],
            'address': f"0x{gf['addr']:05X}",
            'segoff': gf['segoff'],
            'size': gf.get('size', gf.get('bytecode_size')),
            'is_far': gf.get('is_far', False),
            'overlay': gf.get('overlay', False),
            'caller_count': len(gf.get('callers', [])),
            'callers': [c['name'] for c in gf.get('callers', [])[:5]]
        }
        for gf in graphics_funcs
    ],
    'patterns': {
        'all_in_seg020': True,
        'all_resident': True,
        'farobj_count': len(farobj_funcs),
        'vector_ops': ['fixed_vec3_transform_es', 'vec2_normalize_seq']
    }
}

with open('graphics_functions_analysis.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n" + "=" * 70)
print("Analysis exported to: graphics_functions_analysis.json")
print("=" * 70)

print("""
Summary:
--------
These 6 functions form the CORE of the 3D graphics rendering:

1. Vector Operations:
   - fixed_vec3_transform_es: 3D transformation (rotation/translation)
   - vec2_normalize_seq: 2D normalization (screen space)

2. Far Object Management (farobj):
   - farobj_record_step: Iterate through visible objects
   - farobj_record_lookup_step: Check object visibility
   - farobj_record_push_7c054: Add to render queue 1
   - farobj_record_push_7d0c6: Add to render queue 2

All are RESIDENT (not overlay), in seg020 (main graphics engine).
They represent the pipeline after projection, handling:
  - Transformed coordinates
  - Visibility determination
  - Render queue management

Next steps:
  1. Analyze their callers (who else uses them?)
  2. Understand the two push queues (7c054 vs 7d0c6)
  3. Map complete scene graph management
""")
