"""
Analyze sub_21657 - the only unnamed caller of fixed_vec3_transform_es.

This is a 97-byte function at seg020:1F97. Let's figure out what it does.
"""

import json

# Load data
with open('segment_map.json') as f:
    seg_map = json.load(f)

with open('../ida_falconcd/function_bytes.json') as f:
    func_bytes = json.load(f)

print("=" * 70)
print("sub_21657 Analysis - The Unnamed vec3 Caller")
print("=" * 70)

# Get function data
fdata = func_bytes.get('sub_21657')
if not fdata:
    print("Error: sub_21657 not found!")
    exit(1)

addr = fdata['ea']
bytes_hex = fdata['bytes']
bytecode = bytes([int(bytes_hex[i:i+2], 16) for i in range(0, len(bytes_hex), 2)])

print(f"\nBasic Info:")
print(f"  Address: 0x{addr:05X} (seg020:1F97)")
print(f"  Size: {len(bytecode)} bytes")
print(f"  Is far: {fdata.get('is_far', False)}")
print(f"  Overlay: {fdata.get('overlay', False)}")

# Find all CALL instructions
calls = []
i = 0
while i < len(bytecode):
    if bytecode[i] == 0xE8:  # CALL near
        if i + 2 < len(bytecode):
            offset = bytecode[i+1] + (bytecode[i+2] << 8)
            if offset >= 0x8000:
                offset = offset - 0x10000
            next_inst = addr + i + 3
            target = next_inst + offset
            calls.append({
                'offset': i,
                'target': target,
                'rel_offset': offset
            })
        i += 3
    else:
        i += 1

print(f"\nCalls: {len(calls)}")
for call in calls:
    # Find target name
    target_name = None
    for fname, fdata2 in func_bytes.items():
        if fdata2['ea'] == call['target']:
            # Check segment_map for real name
            for func in seg_map['functions']:
                if func['start_ea'] == call['target']:
                    target_name = func['name']
                    break
            if not target_name:
                target_name = fname
            break
    
    print(f"  +0x{call['offset']:02X}: 0x{call['target']:05X} -> {target_name or 'unknown'}")

# Check who calls sub_21657
print(f"\nCallers of sub_21657:")
callers = []
target = addr

for fname, fdata2 in func_bytes.items():
    if fname == 'sub_21657':
        continue
    
    bytes_hex2 = fdata2['bytes']
    fbytes = bytes([int(bytes_hex2[i:i+2], 16) for i in range(0, len(bytes_hex2), 2)])
    
    for i in range(len(fbytes) - 2):
        if fbytes[i] == 0xE8:
            offset = fbytes[i+1] + (fbytes[i+2] << 8)
            if offset >= 0x8000:
                offset = offset - 0x10000
            next_inst = fdata2['ea'] + i + 3
            call_target = next_inst + offset
            
            if call_target == target:
                # Find real name
                real_name = fname
                for func in seg_map['functions']:
                    if func['start_ea'] == fdata2['ea']:
                        real_name = func['name']
                        break
                
                callers.append({
                    'name': real_name,
                    'ea': fdata2['ea']
                })
                break

if callers:
    print(f"  Found {len(callers)} caller(s):")
    for caller in callers[:10]:
        # Find segoff
        segoff = None
        for func in seg_map['functions']:
            if func['start_ea'] == caller['ea']:
                segoff = func['segoff']
                break
        print(f"    - {caller['name']:<40} ({segoff or '?'})")
else:
    print("  No callers found (might be called indirectly)")

# Check multi-entry points
print(f"\nMulti-entry point analysis:")
multi_entries = seg_map['multi_entry_functions'].get('sub_21657', [])
if multi_entries:
    print(f"  Has {len(multi_entries)} secondary entry points:")
    for entry in multi_entries:
        print(f"    {entry['segoff']} (+0x{entry['offset_from_start']:04X}): {entry['xref_count']} xrefs")
else:
    print("  No secondary entry points")

# Analyze bytecode patterns
print(f"\n" + "=" * 70)
print("Bytecode Analysis")
print("=" * 70)

# Count operation types
mul_count = sum(1 for i in range(len(bytecode)-1) 
               if bytecode[i] in [0xF6, 0xF7] and 
                  ((bytecode[i+1] >> 3) & 7) in [4, 5])
div_count = sum(1 for i in range(len(bytecode)-1) 
               if bytecode[i] in [0xF6, 0xF7] and 
                  ((bytecode[i+1] >> 3) & 7) in [6, 7])
shift_count = sum(1 for b in bytecode if b in [0xD0, 0xD1, 0xD2, 0xD3, 0xC0, 0xC1])
loop_count = sum(1 for b in bytecode if b in [0xE0, 0xE1, 0xE2])

print(f"\nOperation counts:")
print(f"  CALL instructions: {len(calls)}")
print(f"  MUL/IMUL: {mul_count}")
print(f"  DIV/IDIV: {div_count}")
print(f"  Shifts: {shift_count}")
print(f"  LOOP: {loop_count}")

# Show first 64 bytes as hex dump
print(f"\nFirst 64 bytes (hex dump):")
for i in range(0, min(64, len(bytecode)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in bytecode[i:i+16])
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in bytecode[i:i+16])
    print(f"  {addr+i:05X}: {hex_str:<48} {ascii_str}")

# Simple disassembly of key instructions
print(f"\n" + "=" * 70)
print("Key Instruction Patterns")
print("=" * 70)

# Look for common patterns
print(f"\nAnalyzing structure...")

# Check for prologue
if bytecode[0] == 0x55:  # push bp
    print("  [+] Standard function prologue (push bp)")
if len(bytecode) > 1 and bytecode[0:2] == bytes([0x55, 0x8B]):
    print("  [+] Likely: push bp; mov bp, sp")

# Check for stack frame
if 0x83 in bytecode[:10] and 0xEC in bytecode[:10]:  # sub sp, xx
    print("  [+] Allocates stack frame (sub sp, ...)")

# Check for epilogue
if bytecode[-1] == 0xC3 or bytecode[-1] == 0xCB:
    print(f"  [+] Standard epilogue ({'ret' if bytecode[-1] == 0xC3 else 'retf'})")
if 0x5D in bytecode[-5:]:  # pop bp
    print("  [+] Restores base pointer (pop bp)")

# Look for data access patterns
segment_overrides = []
for i in range(len(bytecode)):
    if bytecode[i] in [0x26, 0x2E, 0x36, 0x3E]:  # ES:, CS:, SS:, DS:
        segment_overrides.append(i)

if segment_overrides:
    print(f"\n  [+] Segment overrides found at: {segment_overrides[:5]}")

# Naming suggestions
print(f"\n" + "=" * 70)
print("Naming Suggestions")
print("=" * 70)

print(f"\nBased on analysis:")
print(f"  - Small function (97 bytes)")
print(f"  - Calls fixed_vec3_transform_es (3D transformation)")
print(f"  - Called by {len(callers)} other function(s)")

if calls:
    print(f"\n  Function call pattern suggests:")
    if len(calls) == 1:
        print(f"    -> Simple wrapper or adapter")
    elif len(calls) > 3:
        print(f"    -> Processing pipeline with multiple operations")

# Check if it's near other functions
print(f"\n" + "=" * 70)
print("Context - Nearby Functions")
print("=" * 70)

print(f"\nFunctions near sub_21657 (seg020:1F97):")
nearby = []
for func in seg_map['functions']:
    if 'seg020' in func.get('segoff', ''):
        func_addr = func['start_ea']
        if abs(func_addr - addr) < 1000 and func_addr != addr:  # Within 1KB
            distance = func_addr - addr
            nearby.append((func['name'], func['segoff'], distance, func['end_ea'] - func['start_ea']))

nearby.sort(key=lambda x: abs(x[2]))

for name, segoff, dist, size in nearby[:10]:
    direction = "after" if dist > 0 else "before"
    print(f"  {abs(dist):4d} bytes {direction}: {name:<40} ({segoff}, {size} bytes)")

# Make naming recommendation
print(f"\n" + "=" * 70)
print("Recommendation")
print("=" * 70)

if callers:
    print(f"\nPrimary caller(s): {', '.join(c['name'] for c in callers[:3])}")

print(f"\nSuggested investigation:")
print(f"1. Check in IDA what the callers do with this function")
print(f"2. Examine the parameters passed")
print(f"3. Look at nearby functions for context clues")
print(f"4. Disassemble completely in IDA to understand logic")

print(f"\nPossible names based on context:")
print(f"  - vec3_transform_wrapper")
print(f"  - object_transform_helper")
print(f"  - coord_transform_adapter")
print(f"  - [Context from caller would help]")

# Export analysis
output = {
    'name': 'sub_21657',
    'address': f'0x{addr:05X}',
    'segoff': 'seg020:1F97',
    'size': len(bytecode),
    'calls_to': [
        {
            'offset': f'+0x{c["offset"]:02X}',
            'target': f'0x{c["target"]:05X}',
            'target_name': next((f['name'] for f in seg_map['functions'] if f['start_ea'] == c['target']), 'unknown')
        }
        for c in calls
    ],
    'called_by': [
        {
            'name': c['name'],
            'address': f'0x{c["ea"]:05X}'
        }
        for c in callers
    ],
    'patterns': {
        'mul_count': mul_count,
        'shift_count': shift_count,
        'calls': len(calls),
        'has_prologue': bytecode[0] == 0x55,
        'has_epilogue': bytecode[-1] in [0xC3, 0xCB]
    }
}

with open('sub_21657_analysis.json', 'w') as f:
    json.dump(output, f, indent=2)

print(f"\nAnalysis exported to: sub_21657_analysis.json")
print("=" * 70)
