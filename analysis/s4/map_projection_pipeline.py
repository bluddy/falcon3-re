"""
Map the view_projection transformation pipeline.

This script analyzes the call sequence and data flow to understand
how 3D coordinates are transformed to 2D screen space.

Run after IDA verification to fill in verified operation names.
"""

import json

# Load view_projection bytecode
with open('../ida_falconcd/function_bytes.json') as f:
    func_bytes = json.load(f)

vp = func_bytes.get('sub_20BDB')
if not vp:
    print("Error: view_projection not found!")
    exit(1)

# Convert to bytes
bytecode_hex = vp['bytes']
bytecode = bytes([int(bytecode_hex[i:i+2], 16) for i in range(0, len(bytecode_hex), 2)])
addr = vp['ea']

print("=" * 70)
print("view_projection Pipeline Analysis")
print("=" * 70)
print(f"\nFunction: view_projection (sub_20BDB)")
print(f"Address: 0x{addr:05X} (seg020:151B)")
print(f"Size: {len(bytecode)} bytes")

# Find all CALL instructions
calls = []
i = 0
while i < len(bytecode):
    if bytecode[i] == 0xE8:  # CALL near rel16
        if i + 2 < len(bytecode):
            offset = bytecode[i+1] + (bytecode[i+2] << 8)
            if offset >= 0x8000:
                offset = offset - 0x10000
            next_inst = addr + i + 3
            target = next_inst + offset
            calls.append({
                'offset_in_func': i,
                'address': addr + i,
                'target': target,
                'rel_offset': offset
            })
        i += 3
    else:
        i += 1

print(f"\nFound {len(calls)} CALL instructions")
print("\n" + "=" * 70)
print("Call Sequence (in execution order)")
print("=" * 70)

# Map targets to our identified functions
target_map = {
    0x1CC57: {'name': 'seg015:0C65', 'identified_as': 'math_segment_setup', 'confidence': 'HIGH'},
    0x1CC6C: {'name': 'seg015:0C7A', 'identified_as': 'math_complex_dispatcher', 'confidence': 'LOW'},
    0x1CCCD: {'name': 'seg015:0CDB', 'identified_as': 'fixed_shift_left_32', 'confidence': 'HIGH'},
    0x1CCE2: {'name': 'seg015:0CF0', 'identified_as': 'math_farcall_wrapper', 'confidence': 'MEDIUM'},
    0x1CD43: {'name': 'seg015:0D51', 'identified_as': 'math_call_with_cleanup', 'confidence': 'HIGH'},
    0x1CD58: {'name': 'seg015:0D66', 'identified_as': 'math_conditional_op', 'confidence': 'MEDIUM'},
    0x1D894: {'name': 'seg017:01FE', 'identified_as': 'table_lookup_32bit', 'confidence': 'VERY HIGH'},
    0x1D8B2: {'name': 'seg017:021C', 'identified_as': 'multiply_accumulate_loop', 'confidence': 'HIGH'},
    0x1D879: {'name': 'seg017:01E3', 'identified_as': 'function_epilogue_cond', 'confidence': 'VERY HIGH'},
    0x210EF: {'name': 'seg020:1A2F', 'identified_as': 'abs_value_32bit', 'confidence': 'HIGH'},
}

print(f"{'#':<4} {'Offset':<8} {'Target':<12} {'Function':<20} {'Identified As':<30} {'Conf'}")
print("-" * 100)

for idx, call in enumerate(calls, 1):
    target = call['target']
    info = target_map.get(target, {'name': f"0x{target:05X}", 'identified_as': 'UNKNOWN', 'confidence': '?'})
    
    print(f"{idx:<4} +0x{call['offset_in_func']:04X}  0x{target:05X}  {info['name']:<20} "
          f"{info['identified_as']:<30} {info['confidence']}")

# Analyze call patterns
print("\n" + "=" * 70)
print("Pipeline Stage Analysis")
print("=" * 70)

print("""
Based on call sequence, we can infer the transformation pipeline:

Stage 1: Setup & Initialization
  - Calls to segment setup functions
  - Data structure initialization
  - Parameter loading

Stage 2: Coordinate Transformation
  - Multiple math operations
  - Likely: rotation, translation, scaling
  - 32-bit fixed-point arithmetic

Stage 3: Projection
  - Perspective division
  - Screen space conversion
  - Clipping checks

Stage 4: Output
  - Store results
  - Return to caller
""")

# Group calls by likely pipeline stage
print("\nDetailed Stage Breakdown:")
print("-" * 70)

stages = {
    'Setup': [],
    'Transform': [],
    'Project': [],
    'Output': []
}

# Heuristic classification
for idx, call in enumerate(calls, 1):
    target = call['target']
    info = target_map.get(target, {'identified_as': 'UNKNOWN'})
    identified = info['identified_as']
    
    # Classify by operation type
    if 'setup' in identified or idx == 1:
        stages['Setup'].append((idx, call, info))
    elif 'epilogue' in identified or 'return' in identified:
        stages['Output'].append((idx, call, info))
    elif 'table_lookup' in identified or 'abs' in identified:
        stages['Project'].append((idx, call, info))
    else:
        stages['Transform'].append((idx, call, info))

for stage_name, stage_calls in stages.items():
    if stage_calls:
        print(f"\n{stage_name} Stage:")
        for idx, call, info in stage_calls:
            name = info.get('name', f"0x{call['target']:05X}")
            identified = info.get('identified_as', 'UNKNOWN')
            print(f"  {idx}. +0x{call['offset_in_func']:04X}: {name} - {identified}")

# Data flow analysis
print("\n" + "=" * 70)
print("Data Flow Analysis")
print("=" * 70)

print("""
Input (from caller sub_256A3):
  DI register = pointer to structure at DGROUP:0x4287
  Structure likely contains:
    [di+0x00] : X coordinate (32-bit?)
    [di+0x02] : Y coordinate (32-bit?)
    [di+0x04] : Z coordinate (32-bit?)
    [di+0x20] : Additional data
    [di+0x24] : Flags (tested for 0x0080)

Intermediate Values:
  Stack variables: [bp-2], [bp-4], etc.
  Register usage: AX, DX, CX, BX, SI, DI
  Segment ES: Points to data segment 0x7772

Output:
  Likely written back to structure at [di+xx]
  Or returned in registers
  Or written to separate output buffer
""")

# Recommendations
print("\n" + "=" * 70)
print("Verification Recommendations")
print("=" * 70)

print("""
To complete the pipeline understanding:

1. In IDA, step through view_projection with a debugger:
   - Set breakpoint at seg020:151B (view_projection entry)
   - Examine DI register (input structure)
   - Step through each CALL
   - Watch register/memory changes

2. Identify input parameters:
   - What's in the structure at DGROUP:0x4287?
   - Are coordinates 16-bit or 32-bit?
   - What's the fixed-point scale?

3. Map intermediate transformations:
   - After each math call, what changed?
   - What matrix/rotation is applied?
   - When does perspective division happen?

4. Verify output location:
   - Where are final screen coordinates stored?
   - Format: 16-bit? Pixel coordinates?

5. Check for error conditions:
   - What happens if Z <= 0 (behind camera)?
   - Clipping logic?
   - Off-screen handling?
""")

# Export pipeline map
pipeline_map = {
    'function': 'view_projection',
    'address': f"0x{addr:05X}",
    'size': len(bytecode),
    'call_count': len(calls),
    'calls': [
        {
            'sequence': idx,
            'offset': call['offset_in_func'],
            'target': f"0x{call['target']:05X}",
            'function': target_map.get(call['target'], {}).get('name', 'unknown'),
            'operation': target_map.get(call['target'], {}).get('identified_as', 'unknown'),
            'confidence': target_map.get(call['target'], {}).get('confidence', '?')
        }
        for idx, call in enumerate(calls, 1)
    ],
    'input_structure': {
        'register': 'DI',
        'location': 'DGROUP:0x4287',
        'fields': {
            'offset_0x00': '32-bit X coordinate?',
            'offset_0x02': '32-bit Y coordinate?',
            'offset_0x04': '32-bit Z coordinate?',
            'offset_0x20': 'unknown',
            'offset_0x24': 'flags (0x0080 tested)'
        }
    },
    'data_segment': {
        'segment': '0x7772',
        'table_offset': '0x0F34',
        'table_type': 'likely sin/cos or perspective table'
    }
}

with open('projection_pipeline_map.json', 'w') as f:
    json.dump(pipeline_map, f, indent=2)

print("\n" + "=" * 70)
print("Pipeline map exported to: projection_pipeline_map.json")
print("=" * 70)
