"""
Analyze view_projection (sub_20BDB at seg020:151B, 0x20BDB)

This function is called by sub_256A3 which accesses DGROUP:0x4287.
Let's understand what it does.
"""

import json
from pathlib import Path

print("=" * 70)
print("view_projection (sub_20BDB) Analysis")
print("=" * 70)

# Load segment map
with open('segment_map.json') as f:
    seg_map = json.load(f)

# Load function bytes
with open('../ida_falconcd/function_bytes.json') as f:
    func_bytes = json.load(f)

# Get view_projection info
vp = func_bytes.get('sub_20BDB')
if not vp:
    print("ERROR: sub_20BDB not found!")
    exit(1)

print(f"\nBasic Info:")
print(f"  Linear address: 0x{vp['ea']:X}")
print(f"  Size: {vp['size']} bytes")
print(f"  Is far call: {vp['is_far']}")
print(f"  In overlay: {vp['overlay']}")

# Convert to bytes
bytes_hex = vp['bytes']
bytecode = bytes([int(bytes_hex[i:i+2], 16) for i in range(0, len(bytes_hex), 2)])

print(f"\nFirst 64 bytes (hex):")
for i in range(0, min(64, len(bytecode)), 16):
    hex_str = ' '.join(f'{b:02X}' for b in bytecode[i:i+16])
    print(f"  {i:04X}: {hex_str}")

# Look for interesting patterns
print(f"\nPattern Analysis:")

# DGROUP accesses (segment override CS: 0x2E or DS: 0x3E)
dgroup_accesses = []
for i in range(len(bytecode) - 4):
    # Look for segment overrides followed by memory access
    if bytecode[i] == 0x2E:  # CS: override
        # mov [mem], reg (89 xx or 88 xx)
        if i + 3 < len(bytecode) and bytecode[i+1] in [0x89, 0x88, 0x8B, 0x8A]:
            addr = bytecode[i+2] + (bytecode[i+3] << 8)
            dgroup_accesses.append({
                'offset': i,
                'type': 'CS: override',
                'addr': addr,
                'instruction': bytecode[i:i+4].hex()
            })

print(f"  DGROUP accesses: {len(dgroup_accesses)}")
if dgroup_accesses:
    print(f"  First few:")
    for access in dgroup_accesses[:5]:
        print(f"    +{access['offset']:04X}: {access['type']} [0x{access['addr']:04X}] - {access['instruction']}")

# Look for CALL instructions
calls = []
for i in range(len(bytecode) - 2):
    if bytecode[i] == 0xE8:  # CALL near rel16
        offset = bytecode[i+1] + (bytecode[i+2] << 8)
        if offset & 0x8000:
            offset = offset - 0x10000
        next_inst = vp['ea'] + i + 3
        target = next_inst + offset
        calls.append({
            'offset': i,
            'target': target,
            'rel': offset
        })

print(f"\n  CALL instructions: {len(calls)}")
if calls:
    print(f"  Targets:")
    for call in calls[:10]:  # First 10
        target = call['target']
        # Find function name
        fname = None
        for name, data in func_bytes.items():
            if data['ea'] == target:
                fname = name
                break
        
        if not fname:
            # Check segment map
            for func in seg_map['functions']:
                if func['start_ea'] == target:
                    fname = func['name']
                    break
        
        segoff = None
        for seg in seg_map['segments']:
            if seg['start_ea'] <= target < seg['end_ea']:
                offset = target - seg['start_ea']
                segoff = f"{seg['name']}:{offset:04X}"
                break
        
        print(f"    +{call['offset']:04X}: 0x{target:05X} ({segoff or '?'}) -> {fname or 'unknown'}")

# Check who calls view_projection
print(f"\nCallers of view_projection:")

# We know sub_256A3 calls it
print(f"  - sub_256A3 (seg020:5FE3, 0x256A3) - accesses DGROUP:0x4287")

# Search for other callers in function_bytes
callers = []
for fname, fdata in func_bytes.items():
    if fname == 'sub_20BDB':
        continue
    
    bytes_hex = fdata['bytes']
    fbytes = bytes([int(bytes_hex[i:i+2], 16) for i in range(0, len(bytes_hex), 2)])
    
    for i in range(len(fbytes) - 2):
        if fbytes[i] == 0xE8:
            offset = fbytes[i+1] + (fbytes[i+2] << 8)
            if offset & 0x8000:
                offset = offset - 0x10000
            next_inst = fdata['ea'] + i + 3
            target = next_inst + offset
            
            if target == 0x20BDB:
                callers.append({
                    'name': fname,
                    'ea': fdata['ea'],
                    'call_offset': i
                })
                break

if callers:
    print(f"\nFound {len(callers)} callers in function_bytes.json:")
    for caller in callers[:20]:
        segoff = None
        for seg in seg_map['segments']:
            ea = caller['ea']
            if seg['start_ea'] <= ea < seg['end_ea']:
                offset = ea - seg['start_ea']
                segoff = f"{seg['name']}:{offset:04X}"
                break
        print(f"  - {caller['name']} ({segoff or '?'}, 0x{caller['ea']:X}) at +{caller['call_offset']:04X}")
else:
    print("  No other callers found in function_bytes.json")
    print("  (May be called via function pointers or from other overlays)")

print("\n" + "=" * 70)
print("Next Steps:")
print("=" * 70)
print("1. Disassemble view_projection in IDA (seg020:151B)")
print("2. Understand what it does with data from callers")
print("3. Trace DGROUP:0x4287 usage")
print("4. Check if it's related to 3D projection/transformation")
