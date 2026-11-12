"""
Analyze the 10 callers of fixed_vec3_transform_es.

This function is called 10 times - more than any other graphics function.
Understanding its callers will reveal the rendering architecture.
"""

import json

# Load data
with open('segment_map.json') as f:
    seg_map = json.load(f)

with open('../ida_falconcd/function_bytes.json') as f:
    func_bytes = json.load(f)

# The 10 callers
callers = [
    'sub_1F769',  # seg020:00A9
    'sub_1FB3C',  # seg020:047C - this is record_xform_apply!
    'sub_20BDB',  # seg020:151B - this is view_projection!
    'sub_21657',  # seg020:1F97
    'sub_236C8',  # seg020:4008
    'sub_248CD',  # seg020:520D
    'sub_26B2E',  # seg020:746E
    'sub_28496',  # seg020:8DD6
    'sub_28503',  # seg020:8E43
    'sub_286CE',  # seg020:900E
]

print("=" * 70)
print("fixed_vec3_transform_es Callers Analysis")
print("=" * 70)

# Get info for each caller
caller_info = []

for caller_name in callers:
    fdata = func_bytes.get(caller_name)
    if not fdata:
        continue
    
    # Find in segment_map for real name
    real_name = None
    for func in seg_map['functions']:
        if func['start_ea'] == fdata['ea']:
            real_name = func['name']
            break
    
    info = {
        'func_bytes_name': caller_name,
        'real_name': real_name or caller_name,
        'address': fdata['ea'],
        'size': fdata['size'],
        'is_far': fdata.get('is_far', False),
        'overlay': fdata.get('overlay', False)
    }
    
    # Find segoff
    for func in seg_map['functions']:
        if func['start_ea'] == info['address']:
            info['segoff'] = func['segoff']
            break
    
    caller_info.append(info)

# Display table
print(f"\n{'#':<4} {'Function Name':<35} {'SegOff':<18} {'Size':<8} {'Overlay'}")
print("-" * 78)

for idx, info in enumerate(caller_info, 1):
    overlay_str = 'Yes' if info.get('overlay') else 'No'
    print(f"{idx:<4} {info['real_name']:<35} {info.get('segoff', '?'):<18} {info['size']:<8} {overlay_str}")

# Group by type
print("\n" + "=" * 70)
print("Caller Categorization")
print("=" * 70)

well_named = [c for c in caller_info if not c['real_name'].startswith('sub_')]
sub_named = [c for c in caller_info if c['real_name'].startswith('sub_')]

print(f"\nWell-named functions: {len(well_named)}")
for c in well_named:
    print(f"  - {c['real_name']}")

print(f"\nUnnamed functions (sub_XXXXX): {len(sub_named)}")
for c in sub_named:
    print(f"  - {c['real_name']} ({c.get('segoff', '?')})")

# Check how many times each calls vec3_transform
print("\n" + "=" * 70)
print("Call Frequency Analysis")
print("=" * 70)

for info in caller_info:
    caller_name = info['func_bytes_name']
    fdata = func_bytes.get(caller_name)
    if not fdata:
        continue
    
    # Count calls to 0x248D1 (fixed_vec3_transform_es)
    target = 0x248D1
    bytes_hex = fdata['bytes']
    fbytes = bytes([int(bytes_hex[i:i+2], 16) for i in range(0, len(bytes_hex), 2)])
    
    call_count = 0
    for i in range(len(fbytes) - 2):
        if fbytes[i] == 0xE8:
            offset = fbytes[i+1] + (fbytes[i+2] << 8)
            if offset >= 0x8000:
                offset = offset - 0x10000
            next_inst = fdata['ea'] + i + 3
            call_target = next_inst + offset
            
            if call_target == target:
                call_count += 1
    
    info['vec3_calls'] = call_count

print(f"\n{'Function':<35} {'Calls':<8} {'Interpretation'}")
print("-" * 70)

for info in sorted(caller_info, key=lambda x: x.get('vec3_calls', 0), reverse=True):
    calls = info.get('vec3_calls', 0)
    if calls > 1:
        interpretation = "Multiple transforms (batch processing?)"
    elif calls == 1:
        interpretation = "Single transform per call"
    else:
        interpretation = "No direct calls (indirect?)"
    
    print(f"{info['real_name']:<35} {calls:<8} {interpretation}")

# Analyze sizes
print("\n" + "=" * 70)
print("Size Analysis")
print("=" * 70)

sizes = sorted([(c['real_name'], c['size']) for c in caller_info], 
               key=lambda x: x[1], reverse=True)

print(f"\nBy size (largest first):")
for name, size in sizes:
    if size < 100:
        category = "Small (simple wrapper)"
    elif size < 300:
        category = "Medium (processing logic)"
    elif size < 700:
        category = "Large (complex operations)"
    else:
        category = "Very large (major subsystem)"
    
    print(f"  {size:4d} bytes - {name:<35} [{category}]")

# Look for patterns in the names
print("\n" + "=" * 70)
print("Name Pattern Analysis")
print("=" * 70)

print("\nWell-named functions reveal purpose:")
print("  - record_xform_apply: Apply transformation to a record")
print("  - view_projection: View/projection transformation (main pipeline)")
print("\nOther callers (sub_XXXXX) need investigation")

# Check if any of these are in our top overlay targets
with open('top_overlay_targets.json') as f:
    top_targets = json.load(f)

print("\n" + "=" * 70)
print("Overlay Analysis")
print("=" * 70)

print("\nChecking if any are hot overlay targets...")
found_any = False
if isinstance(top_targets, list):
    for info in caller_info:
        addr_hex = f"0x{info['address']:X}"
        for target in top_targets:
            if isinstance(target, dict):
                if target.get('addr') == addr_hex or target.get('name') == info['func_bytes_name']:
                    print(f"  [!] {info['real_name']} - {target.get('dyn', 0)} dynamic calls")
                    info['dyn_calls'] = target.get('dyn', 0)
                    found_any = True
                    break

if not found_any:
    print("  None of these callers appear in top overlay targets")
    print("  -> They are called statically, not through overlays")

# Export results
output = {
    'target_function': {
        'name': 'fixed_vec3_transform_es',
        'address': '0x248D1',
        'segoff': 'seg020:5211',
        'purpose': '3D vector transformation with fixed-point arithmetic'
    },
    'callers': [
        {
            'name': c['real_name'],
            'address': f"0x{c['address']:X}",
            'segoff': c.get('segoff', 'unknown'),
            'size': c['size'],
            'calls_to_vec3': c.get('vec3_calls', 0),
            'overlay': c.get('overlay', False)
        }
        for c in caller_info
    ],
    'summary': {
        'total_callers': len(caller_info),
        'well_named': len(well_named),
        'unnamed': len(sub_named),
        'largest_caller': max([(c['real_name'], c['size']) for c in caller_info], key=lambda x: x[1])
    }
}

with open('vec3_transform_callers.json', 'w') as f:
    json.dump(output, f, indent=2)

print("\n" + "=" * 70)
print("Recommendations")
print("=" * 70)

print("""
fixed_vec3_transform_es is a CENTRAL operation in the graphics engine.

Priority actions:
1. Name the 8 unnamed callers (sub_XXXXX functions)
2. Understand what each caller does with the transformation
3. Map the transformation parameters (what goes in, what comes out)

Likely caller purposes based on size:
  - Small (< 100 bytes): Simple wrappers, pass-through
  - Medium (100-300): Process single object/vertex
  - Large (300-700): Batch processing, loops
  - Very large (> 700): Major rendering subsystem

The fact that 10 functions need 3D transformation suggests:
  - Multiple rendering paths (terrain, objects, HUD, etc.)
  - Different coordinate spaces (world, view, screen)
  - Various optimization strategies

Next: Analyze one of the large unnamed callers to understand the pattern.
""")

print(f"\nAnalysis exported to: vec3_transform_callers.json")
print("=" * 70)
