"""
Extract bytecode for each of the 10 math helper entry points.

We'll extract enough bytes from each entry point to analyze the operation.
"""

import json
from pathlib import Path

# Load data
with open('../ida_falconcd/function_bytes.json') as f:
    func_bytes = json.load(f)

# Entry points we're investigating
# Note: function_bytes.json uses sub_XXXXX names, segment_map.json has descriptive names
entry_points = [
    {'addr': 0x1CC57, 'segoff': 'seg015:0C65', 'parent': 'sub_1CC2D', 'parent_ea': 0x1CC2D, 'offset': 0x002A, 'desc_name': 'stream_command_interpret'},
    {'addr': 0x1CC6C, 'segoff': 'seg015:0C7A', 'parent': 'sub_1CC2D', 'parent_ea': 0x1CC2D, 'offset': 0x003F, 'desc_name': 'stream_command_interpret'},
    {'addr': 0x1CCCD, 'segoff': 'seg015:0CDB', 'parent': 'sub_1CC2D', 'parent_ea': 0x1CC2D, 'offset': 0x00A0, 'desc_name': 'stream_command_interpret'},
    {'addr': 0x1CCE2, 'segoff': 'seg015:0CF0', 'parent': 'sub_1CC2D', 'parent_ea': 0x1CC2D, 'offset': 0x00B5, 'desc_name': 'stream_command_interpret'},
    {'addr': 0x1CD43, 'segoff': 'seg015:0D51', 'parent': 'sub_1CC2D', 'parent_ea': 0x1CC2D, 'offset': 0x0116, 'desc_name': 'stream_command_interpret'},
    {'addr': 0x1CD58, 'segoff': 'seg015:0D66', 'parent': 'sub_1CC2D', 'parent_ea': 0x1CC2D, 'offset': 0x012B, 'desc_name': 'stream_command_interpret'},
    {'addr': 0x1D894, 'segoff': 'seg017:01FE', 'parent': 'sub_1D88C', 'parent_ea': 0x1D88C, 'offset': 0x0008, 'desc_name': 'group_children_release'},
    {'addr': 0x1D8B2, 'segoff': 'seg017:021C', 'parent': 'sub_1D88C', 'parent_ea': 0x1D88C, 'offset': 0x0026, 'desc_name': 'group_children_release'},
    {'addr': 0x1D879, 'segoff': 'seg017:01E3', 'parent': 'sub_1D7DA', 'parent_ea': 0x1D7DA, 'offset': 0x009F, 'desc_name': 'channel_list_register_batch'},
    {'addr': 0x210EF, 'segoff': 'seg020:1A2F', 'parent': 'sub_2100F', 'parent_ea': 0x2100F, 'offset': 0x00E0, 'desc_name': 'vec_delta_norm_1f6ee'},
]

print("=" * 70)
print("Math Helper Bytecode Extraction")
print("=" * 70)

# Get parent functions bytecode
parents = {}
for entry in entry_points:
    parent_name = entry['parent']
    if parent_name not in parents:
        # Find in function_bytes
        for fname, fdata in func_bytes.items():
            if fname == parent_name:
                parents[parent_name] = {
                    'ea': fdata['ea'],
                    'size': fdata['size'],
                    'bytes_hex': fdata['bytes'],
                    'bytes': bytes([int(fdata['bytes'][i:i+2], 16) 
                                  for i in range(0, len(fdata['bytes']), 2)])
                }
                break

print(f"\nLoaded {len(parents)} parent functions")
for name, data in parents.items():
    print(f"  {name}: 0x{data['ea']:05X}, {data['size']} bytes")

# Extract bytecode for each entry point
print("\n" + "=" * 70)
print("Entry Point Bytecode Analysis")
print("=" * 70)

def format_hex(bytecode, addr, max_bytes=48):
    """Format bytecode as hex dump."""
    lines = []
    for i in range(0, min(len(bytecode), max_bytes), 16):
        hex_str = ' '.join(f'{b:02X}' for b in bytecode[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in bytecode[i:i+16])
        lines.append(f"  {addr+i:05X}: {hex_str:<48} {ascii_str}")
    return '\n'.join(lines)

def analyze_operation(bytecode, segoff):
    """Analyze first few bytes to guess operation type."""
    if len(bytecode) < 4:
        return "too short to analyze"
    
    b = bytecode
    hints = []
    
    # Check for common patterns
    if b[0] == 0xC3:
        hints.append("RET (empty stub?)")
    elif b[0] == 0xCB:
        hints.append("RETF (far return)")
    
    # Look for MUL/IMUL
    for i in range(min(10, len(b))):
        if b[i] in [0xF6, 0xF7]:
            if i+1 < len(b):
                modrm = b[i+1]
                op = (modrm >> 3) & 0x7
                if op == 4:
                    hints.append(f"MUL at +{i}")
                elif op == 5:
                    hints.append(f"IMUL at +{i}")
                elif op == 6:
                    hints.append(f"DIV at +{i}")
                elif op == 7:
                    hints.append(f"IDIV at +{i}")
    
    # Look for shifts (fixed-point operations)
    shift_count = sum(1 for byte in b[:20] if byte in [0xD0, 0xD1, 0xD2, 0xD3, 0xC0, 0xC1])
    if shift_count > 2:
        hints.append(f"{shift_count} shift ops (fixed-point?)")
    
    # Look for CALL
    call_count = sum(1 for byte in b[:20] if byte == 0xE8)
    if call_count > 0:
        hints.append(f"{call_count} CALL(s)")
    
    # Look for table access [BX+SI], [BX+DI]
    for i in range(min(10, len(b)-1)):
        if b[i] in [0x8A, 0x8B]:  # MOV
            modrm = b[i+1]
            if (modrm & 0xC7) in [0x00, 0x01]:  # [BX+SI] or [BX+DI]
                hints.append("table lookup")
                break
    
    # Look for LOOP
    if any(byte in b[:20] for byte in [0xE0, 0xE1, 0xE2]):
        hints.append("has LOOP")
    
    # Size-based guess
    if len(bytecode) < 10:
        hints.append("tiny (inline?)")
    elif len(bytecode) < 30:
        hints.append("small (simple op)")
    elif len(bytecode) < 80:
        hints.append("medium")
    else:
        hints.append("large (complex)")
    
    return ", ".join(hints) if hints else "unknown"

# Process each entry point
results = []

for entry in entry_points:
    parent = parents[entry['parent']]
    offset = entry['offset']
    
    # Extract bytecode from parent function at offset
    # Extract until next entry point or up to 64 bytes
    start = offset
    
    # Find how many bytes until next entry point
    same_parent = [e for e in entry_points if e['parent'] == entry['parent']]
    next_offsets = [e['offset'] for e in same_parent if e['offset'] > offset]
    
    if next_offsets:
        end = min(next_offsets)
        size = end - start
    else:
        # Last entry in this parent, extract up to 64 bytes or end of function
        size = min(64, parent['size'] - start)
    
    bytecode = parent['bytes'][start:start+size]
    
    analysis = analyze_operation(bytecode, entry['addr'])
    
    result = {
        'segoff': entry['segoff'],
        'address': entry['addr'],
        'parent': entry['parent'],
        'offset': offset,
        'size': len(bytecode),
        'analysis': analysis,
        'bytecode_hex': bytecode.hex()
    }
    results.append(result)
    
    print(f"\n{entry['segoff']} (0x{entry['addr']:05X})")
    print(f"  Parent: {entry['parent']} +0x{offset:04X}")
    print(f"  Size: {len(bytecode)} bytes")
    print(f"  Analysis: {analysis}")
    print(f"\nHex dump:")
    print(format_hex(bytecode, entry['addr'], 48))

# Look for patterns
print("\n" + "=" * 70)
print("Pattern Summary")
print("=" * 70)

mul_funcs = [r for r in results if 'MUL' in r['analysis'] or 'IMUL' in r['analysis']]
div_funcs = [r for r in results if 'DIV' in r['analysis'] or 'IDIV' in r['analysis']]
shift_funcs = [r for r in results if 'shift' in r['analysis']]
table_funcs = [r for r in results if 'table' in r['analysis']]
call_funcs = [r for r in results if 'CALL' in r['analysis']]

print(f"\nMultiply operations: {len(mul_funcs)}")
for r in mul_funcs:
    print(f"  {r['segoff']}: {r['analysis']}")

print(f"\nDivide operations: {len(div_funcs)}")
for r in div_funcs:
    print(f"  {r['segoff']}: {r['analysis']}")

print(f"\nFixed-point (shift) operations: {len(shift_funcs)}")
for r in shift_funcs:
    print(f"  {r['segoff']}: {r['analysis']}")

print(f"\nTable lookup operations: {len(table_funcs)}")
for r in table_funcs:
    print(f"  {r['segoff']}: {r['analysis']}")

print(f"\nFunctions that make calls: {len(call_funcs)}")
for r in call_funcs:
    print(f"  {r['segoff']}: {r['analysis']}")

# Export results
with open('math_helper_bytecode.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 70)
print("Naming Suggestions Based on Analysis")
print("=" * 70)

suggestions = []

for r in results:
    analysis = r['analysis']
    segoff = r['segoff']
    
    # Try to guess purpose
    if 'IMUL' in analysis and 'shift' in analysis:
        suggestions.append((segoff, 'fixed_point_multiply', analysis))
    elif 'IDIV' in analysis and 'shift' in analysis:
        suggestions.append((segoff, 'fixed_point_divide', analysis))
    elif 'table lookup' in analysis:
        suggestions.append((segoff, 'trig_table_lookup', analysis))
    elif 'IMUL' in analysis:
        suggestions.append((segoff, 'multiply_16bit', analysis))
    elif 'IDIV' in analysis:
        suggestions.append((segoff, 'divide_16bit', analysis))
    elif 'shift' in analysis and 'CALL' not in analysis:
        suggestions.append((segoff, 'bit_shift_helper', analysis))
    elif 'CALL' in analysis:
        suggestions.append((segoff, 'composite_math_op', analysis))
    else:
        suggestions.append((segoff, 'math_helper_unknown', analysis))

print("\nSuggested names:")
for segoff, name, analysis in suggestions:
    print(f"  {segoff:<16} -> {name:<25} ({analysis})")

print("\n" + "=" * 70)
print("Output saved to: math_helper_bytecode.json")
print("=" * 70)

print("""
Next steps:
1. Review hex dumps above for specific patterns
2. Disassemble in IDA to get exact instructions
3. Cross-reference with view_projection calling context
4. Name functions based on actual operations
""")
