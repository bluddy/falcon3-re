#!/usr/bin/env python3
"""
Analyze sub_256A3 and DGROUP:0x4287 structure.

sub_256A3 (10,222 calls):
  push ds
  mov di, 7B0Eh           ; DGROUP runtime segment
  mov ds, di
  mov di, 4287h           ; Offset into DGROUP
  push cs
  call near sub_10BDB     ; Resident function
  pop ds
  retf

Goal: Understand what data structure is at DGROUP:0x4287 and what sub_10BDB does with it.
"""
import json
from pathlib import Path

print("="*80)
print("ANALYZING sub_256A3: DGROUP:0x4287 ACCESSOR")
print("="*80)

# First, let's understand sub_256A3 itself
fb = json.load(open('../ida_falconcd/function_bytes.json'))

func_data = fb['sub_256A3']
print(f"\nsub_256A3 details:")
print(f"  Address: 0x{func_data['ea']:05X}")
print(f"  Size: {func_data['size']} bytes")
print(f"  Calls: 10,222 (from call frequency analysis)")
print(f"  Bytecode: {func_data['bytes']}")

# Decode the bytecode
bytecode = bytes.fromhex(func_data['bytes'])
print(f"\n  Disassembly:")
print(f"    1E              push ds")
print(f"    BF 0E 7B        mov di, 7B0Eh       ; DGROUP runtime = 0x7B0E")
print(f"    8E DF           mov ds, di")
print(f"    BF 87 42        mov di, 4287h       ; offset = 0x4287")
print(f"    0E              push cs")
print(f"    E8 2B B5        call near 0x10BDB   ; sub_10BDB")
print(f"    1F              pop ds")
print(f"    CB              retf")

# Now let's analyze sub_10BDB
if 'sub_10BDB' in fb:
    sub_10bdb = fb['sub_10BDB']
    print(f"\nsub_10BDB (the accessor function):")
    print(f"  Address: 0x{sub_10bdb['ea']:05X}")
    print(f"  Size: {sub_10bdb['size']} bytes")
    print(f"  Bytecode: {sub_10bdb['bytes']}")
    
    # Decode sub_10BDB
    bdb_bytes = bytes.fromhex(sub_10bdb['bytes'])
    print(f"\n  Raw bytes ({len(bdb_bytes)}):")
    for i in range(0, min(len(bdb_bytes), 64), 16):
        hex_str = ' '.join(f"{bdb_bytes[i+j]:02X}" for j in range(min(16, len(bdb_bytes)-i)))
        print(f"    {hex_str}")
    
    # Try to decode instructions (manual for now)
    print(f"\n  Basic pattern analysis:")
    
    # Check for common patterns
    if b'\x8b' in bdb_bytes[:10]:
        print("    Contains MOV instructions (data access)")
    if b'\x89' in bdb_bytes[:10]:
        print("    Contains MOV instructions (data write)")
    if b'\xa0' in bdb_bytes[:10] or b'\xa1' in bdb_bytes[:10]:
        print("    Contains direct memory access (MOV AX/AL)")
    if b'\x2e' in bdb_bytes:
        print("    Contains CS: segment override")
    if b'\xcb' in bdb_bytes or b'\xc3' in bdb_bytes:
        ret_pos = bdb_bytes.find(b'\xcb') if b'\xcb' in bdb_bytes else bdb_bytes.find(b'\xc3')
        print(f"    Returns at offset {ret_pos}")
else:
    print(f"\nWARNING: sub_10BDB not found in function_bytes.json!")

# Check DGROUP information from findings
print(f"\n" + "="*80)
print("DGROUP CONTEXT")
print("="*80)
print(f"\nFrom Finding 176 (VGRAPH analysis):")
print(f"  DGROUP runtime segment: 0x7B0E (confirmed)")
print(f"  Also referenced as: DS=27687, runtime 0x6C27")
print(f"  This is the main data segment for global variables")

print(f"\nOffset 0x4287 in DGROUP:")
print(f"  Decimal: {0x4287} bytes into DGROUP")
print(f"  This is approximately {0x4287//1024:.1f} KB into the data segment")

# Check if we have DGROUP dumps
dgroup_dumps = list(Path('../../memdump').glob('**/DGROUP*.bin'))
if dgroup_dumps:
    print(f"\n  Found {len(dgroup_dumps)} DGROUP dump(s):")
    for dump in dgroup_dumps[:5]:
        print(f"    {dump}")
else:
    print(f"\n  No DGROUP dumps found in memdump/")

# Look for other functions that access DGROUP:0x4287 or nearby offsets
print(f"\n" + "="*80)
print("SEARCHING FOR RELATED ACCESSORS")
print("="*80)

# Pattern: mov di, 7B0Eh; mov ds, di; mov di, XXXX
# Look for similar patterns in bytecode

target_pattern = bytes.fromhex("BF0E7B8EDFBF")  # mov di,7B0E; mov ds,di; mov di,
similar_funcs = []

for fname, fdata in fb.items():
    fcode = bytes.fromhex(fdata['bytes'])
    if target_pattern in fcode:
        # Extract the offset value (next 2 bytes after pattern)
        pos = fcode.find(target_pattern)
        if pos + len(target_pattern) + 2 <= len(fcode):
            offset_bytes = fcode[pos + len(target_pattern):pos + len(target_pattern) + 2]
            offset_val = int.from_bytes(offset_bytes, 'little')
            similar_funcs.append((fname, offset_val, fdata['ea']))

print(f"\nFunctions with similar DGROUP access pattern:")
print(f"{'Function':<20} {'Offset':<10} {'Address':<12} {'Distance from 0x4287'}")
print("-"*70)

for fname, offset, ea in sorted(similar_funcs, key=lambda x: x[1]):
    dist = offset - 0x4287
    dist_str = f"{dist:+d}" if dist != 0 else "SAME"
    print(f"{fname:<20} 0x{offset:04X}     0x{ea:05X}      {dist_str}")

if similar_funcs:
    # Cluster analysis
    offsets = [off for _, off, _ in similar_funcs]
    print(f"\n  Total accessors found: {len(similar_funcs)}")
    print(f"  Offset range: 0x{min(offsets):04X} - 0x{max(offsets):04X}")
    print(f"  Span: {max(offsets) - min(offsets)} bytes")
    
    # Check if they're clustered (suggests structure array)
    if len(similar_funcs) > 1:
        deltas = sorted(set([similar_funcs[i+1][1] - similar_funcs[i][1] 
                            for i in range(len(similar_funcs)-1)]))
        if deltas:
            print(f"  Common offset deltas: {[hex(d) for d in deltas[:5]]}")
            if len(set(deltas)) < len(deltas) // 2:
                print(f"  -> Suggests structured data (array or table)")

# Summary
print(f"\n" + "="*80)
print("SUMMARY & NEXT STEPS")
print("="*80)
print(f"\nsub_256A3:")
print(f"  - Accesses DGROUP:0x4287 via sub_10BDB")
print(f"  - 10,222 calls = very hot path")
print(f"  - Sets DS=DGROUP, DI=0x4287, calls accessor")

print(f"\nTo identify the data structure:")
print(f"  1. Disassemble sub_10BDB to see what it does with [DS:DI]")
print(f"  2. Check if similar accessors form a pattern (array? struct?)")
print(f"  3. Dump DGROUP:0x4287 from memory dumps to see actual data")
print(f"  4. Look for xrefs to sub_256A3 to understand usage context")

print(f"\nPossible structure types (based on frequency):")
print(f"  - Player state (accessed every frame/update)")
print(f"  - Input buffer (keyboard/joystick state)")
print(f"  - Current frame/game state")
print(f"  - Active entity pointer/handle")
print(f"  - Display/render state")

# Save results
output = {
    'function': 'sub_256A3',
    'calls': 10222,
    'dgroup_segment': 0x7B0E,
    'dgroup_offset': 0x4287,
    'accessor_function': 'sub_10BDB',
    'similar_accessors': [
        {'function': f, 'offset': o, 'address': a}
        for f, o, a in similar_funcs
    ]
}

json.dump(output, open('dgroup_4287_analysis.json', 'w'), indent=2)
print(f"\nSaved analysis to dgroup_4287_analysis.json")
