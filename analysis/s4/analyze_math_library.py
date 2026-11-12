"""
Analyze the math library functions in seg015 and seg017.

view_projection calls 16 functions - let's characterize them to understand
the projection pipeline.
"""

import json
from pathlib import Path

print("=" * 70)
print("Math Library Analysis - seg015 & seg017")
print("=" * 70)

# Load data
with open('segment_map.json') as f:
    seg_map = json.load(f)

with open('../ida_falconcd/function_bytes.json') as f:
    func_bytes = json.load(f)

# Targets from view_projection analysis
targets = [
    # seg015 calls
    {'addr': 0x1CC57, 'segoff': 'seg015:0C65'},
    {'addr': 0x1CC6C, 'segoff': 'seg015:0C7A'},
    {'addr': 0x1CCCD, 'segoff': 'seg015:0CDB'},
    {'addr': 0x1CCE2, 'segoff': 'seg015:0CF0'},
    {'addr': 0x1CD43, 'segoff': 'seg015:0D51'},
    {'addr': 0x1CD58, 'segoff': 'seg015:0D66'},
    # seg017 calls
    {'addr': 0x1D8B2, 'segoff': 'seg017:021C'},
    {'addr': 0x1D879, 'segoff': 'seg017:01E3'},
    {'addr': 0x1D894, 'segoff': 'seg017:01FE'},
    # seg020 call
    {'addr': 0x210EF, 'segoff': 'seg020:1A2F'},
]

print("\nFinding functions in segment_map...")

# Find functions in segment map
for target in targets:
    addr = target['addr']
    
    # Find in segment map
    for func in seg_map['functions']:
        if func['start_ea'] == addr:
            target['name'] = func['name']
            target['size'] = func['end_ea'] - func['start_ea']
            target['found_in_segmap'] = True
            break
    else:
        target['found_in_segmap'] = False
        target['name'] = None
        
        # Check if inside a function (multi-entry?)
        for func in seg_map['functions']:
            if func['start_ea'] <= addr < func['end_ea']:
                target['parent_func'] = func['name']
                target['offset_in_parent'] = addr - func['start_ea']
                break

# Find in function_bytes
for target in targets:
    addr = target['addr']
    
    for fname, fdata in func_bytes.items():
        if fdata['ea'] == addr:
            target['func_bytes_name'] = fname
            target['bytecode_size'] = fdata['size']
            target['bytes'] = fdata['bytes']
            break

# Print findings
print("\n" + "=" * 70)
print("FUNCTION CATALOG")
print("=" * 70)

seg015_funcs = [t for t in targets if t['segoff'].startswith('seg015:')]
seg017_funcs = [t for t in targets if t['segoff'].startswith('seg017:')]
seg020_funcs = [t for t in targets if t['segoff'].startswith('seg020:')]

print(f"\nseg015 Functions (6 calls):")
print("-" * 70)
for t in seg015_funcs:
    name = t.get('name') or t.get('func_bytes_name') or 'UNKNOWN'
    size = t.get('size') or t.get('bytecode_size') or '?'
    print(f"{t['segoff']:<16} 0x{t['addr']:05X}  {name:<30} {size:>4} bytes")
    if 'parent_func' in t:
        print(f"                     -> Inside {t['parent_func']} at +0x{t['offset_in_parent']:04X}")

print(f"\nseg017 Functions (3 calls):")
print("-" * 70)
for t in seg017_funcs:
    name = t.get('name') or t.get('func_bytes_name') or 'UNKNOWN'
    size = t.get('size') or t.get('bytecode_size') or '?'
    print(f"{t['segoff']:<16} 0x{t['addr']:05X}  {name:<30} {size:>4} bytes")
    if 'parent_func' in t:
        print(f"                     -> Inside {t['parent_func']} at +0x{t['offset_in_parent']:04X}")

print(f"\nseg020 Functions (1 call):")
print("-" * 70)
for t in seg020_funcs:
    name = t.get('name') or t.get('func_bytes_name') or 'UNKNOWN'
    size = t.get('size') or t.get('bytecode_size') or '?'
    print(f"{t['segoff']:<16} 0x{t['addr']:05X}  {name:<30} {size:>4} bytes")
    if 'parent_func' in t:
        print(f"                     -> Inside {t['parent_func']} at +0x{t['offset_in_parent']:04X}")

# Analyze bytecode patterns
print("\n" + "=" * 70)
print("BYTECODE ANALYSIS")
print("=" * 70)

def analyze_bytecode(bytecode_hex, name, addr):
    """Analyze function bytecode for patterns."""
    if not bytecode_hex:
        return None
    
    bytecode = bytes([int(bytecode_hex[i:i+2], 16) for i in range(0, len(bytecode_hex), 2)])
    
    analysis = {
        'name': name,
        'addr': addr,
        'size': len(bytecode),
        'has_mul': False,
        'has_div': False,
        'has_shift': False,
        'has_loop': False,
        'has_table_lookup': False,
        'calls': []
    }
    
    # Scan for patterns
    for i in range(len(bytecode)):
        b = bytecode[i]
        
        # MUL/IMUL (F6/F7 with appropriate ModR/M)
        if b in [0xF6, 0xF7]:
            if i + 1 < len(bytecode):
                modrm = bytecode[i + 1]
                opcode_ext = (modrm >> 3) & 0x7
                if opcode_ext in [4, 5]:  # MUL=4, IMUL=5
                    analysis['has_mul'] = True
        
        # DIV/IDIV
        if b in [0xF6, 0xF7]:
            if i + 1 < len(bytecode):
                modrm = bytecode[i + 1]
                opcode_ext = (modrm >> 3) & 0x7
                if opcode_ext in [6, 7]:  # DIV=6, IDIV=7
                    analysis['has_div'] = True
        
        # Shift operations (D0-D3, C0-C1)
        if b in [0xD0, 0xD1, 0xD2, 0xD3, 0xC0, 0xC1]:
            analysis['has_shift'] = True
        
        # LOOP instructions
        if b in [0xE0, 0xE1, 0xE2]:
            analysis['has_loop'] = True
        
        # Table lookup pattern: mov reg, [bx+si] or similar
        if b == 0x8A or b == 0x8B:
            if i + 1 < len(bytecode):
                modrm = bytecode[i + 1]
                # Check for [BX+SI] or [BX+DI] addressing
                if (modrm & 0xC7) in [0x00, 0x01]:
                    analysis['has_table_lookup'] = True
        
        # CALL instructions
        if b == 0xE8:
            if i + 2 < len(bytecode):
                offset = bytecode[i+1] + (bytecode[i+2] << 8)
                if offset & 0x8000:
                    offset = offset - 0x10000
                target = addr + i + 3 + offset
                analysis['calls'].append(target)
    
    return analysis

print("\nPattern Detection:")
print("-" * 70)
print(f"{'Function':<30} {'Size':<6} {'Mul':<5} {'Div':<5} {'Shift':<6} {'Loop':<6} {'Table':<6} {'Calls'}")
print("-" * 70)

analyses = []
for t in targets:
    bytecode = t.get('bytes')
    name = t.get('name') or t.get('func_bytes_name') or f"0x{t['addr']:X}"
    addr = t['addr']
    
    if bytecode:
        result = analyze_bytecode(bytecode, name, addr)
        if result:
            analyses.append(result)
            print(f"{name:<30} {result['size']:<6} "
                  f"{'✓' if result['has_mul'] else ' ':<5} "
                  f"{'✓' if result['has_div'] else ' ':<5} "
                  f"{'✓' if result['has_shift'] else ' ':<6} "
                  f"{'✓' if result['has_loop'] else ' ':<6} "
                  f"{'✓' if result['has_table_lookup'] else ' ':<6} "
                  f"{len(result['calls'])}")

# Categorize functions
print("\n" + "=" * 70)
print("FUNCTION CATEGORIZATION")
print("=" * 70)

multiply_funcs = [a for a in analyses if a['has_mul'] and not a['has_div']]
divide_funcs = [a for a in analyses if a['has_div']]
shift_only = [a for a in analyses if a['has_shift'] and not a['has_mul'] and not a['has_div']]
table_lookup = [a for a in analyses if a['has_table_lookup']]

print(f"\nMultiplication functions ({len(multiply_funcs)}):")
for f in multiply_funcs:
    print(f"  - {f['name']} ({f['size']} bytes)")

print(f"\nDivision functions ({len(divide_funcs)}):")
for f in divide_funcs:
    print(f"  - {f['name']} ({f['size']} bytes)")

print(f"\nShift-only functions ({len(shift_only)}):")
for f in shift_only:
    print(f"  - {f['name']} ({f['size']} bytes)")

print(f"\nTable lookup functions ({len(table_lookup)}):")
for f in table_lookup:
    print(f"  - {f['name']} ({f['size']} bytes)")
    print(f"    -> Likely: sin/cos table, atan2 table, or sqrt table")

# Size analysis
print("\n" + "=" * 70)
print("SIZE ANALYSIS")
print("=" * 70)

sizes = [(a['name'], a['size']) for a in analyses]
sizes.sort(key=lambda x: x[1], reverse=True)

print("\nBy size (largest first):")
for name, size in sizes:
    if size < 20:
        category = "tiny (inline helper)"
    elif size < 50:
        category = "small (simple operation)"
    elif size < 100:
        category = "medium (complex math)"
    else:
        category = "large (table-based or multi-operation)"
    print(f"  {size:3d} bytes - {name:<30} [{category}]")

# Check for common patterns in first few bytes
print("\n" + "=" * 70)
print("FIRST 16 BYTES (Prologue Analysis)")
print("=" * 70)

for t in targets:
    bytecode = t.get('bytes')
    if bytecode and len(bytecode) >= 32:
        name = t.get('name') or t.get('func_bytes_name') or f"0x{t['addr']:X}"
        first_16 = bytecode[:32]
        print(f"\n{name}:")
        print(f"  {first_16}")

# Export results
results = {
    'segments': {
        'seg015': len(seg015_funcs),
        'seg017': len(seg017_funcs),
        'seg020': len(seg020_funcs)
    },
    'functions': []
}

for t in targets:
    func_info = {
        'address': t['addr'],
        'segoff': t['segoff'],
        'name': t.get('name') or t.get('func_bytes_name'),
        'size': t.get('size') or t.get('bytecode_size')
    }
    
    # Add analysis if available
    for a in analyses:
        if a['addr'] == t['addr']:
            func_info['has_mul'] = a['has_mul']
            func_info['has_div'] = a['has_div']
            func_info['has_shift'] = a['has_shift']
            func_info['has_loop'] = a['has_loop']
            func_info['has_table_lookup'] = a['has_table_lookup']
            func_info['call_count'] = len(a['calls'])
            break
    
    results['functions'].append(func_info)

with open('math_library_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "=" * 70)
print("CONCLUSIONS")
print("=" * 70)

print(f"""
Math Library Profile:
  - seg015: {len(seg015_funcs)} functions (primary math library)
  - seg017: {len(seg017_funcs)} functions (secondary math/graphics)
  - seg020: {len(seg020_funcs)} function (local helper)

Operation Mix:
  - Multiplication: {len(multiply_funcs)} functions
  - Division: {len(divide_funcs)} functions  
  - Shift-based: {len(shift_only)} functions
  - Table lookups: {len(table_lookup)} functions

Likely Capabilities:
  - Fixed-point arithmetic (mul/div with shifts)
  - Trigonometric tables (table lookup functions)
  - Coordinate transformations (multiple small functions)
  - Perspective division (divide functions)

Next Steps:
  1. Disassemble top 3-5 functions in IDA for detailed analysis
  2. Check for sin/cos/atan2 table patterns
  3. Map function call graph (who calls whom)
  4. Identify fixed-point scaling factors

Output: math_library_analysis.json
""")
