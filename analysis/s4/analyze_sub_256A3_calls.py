"""
Analyze what sub_256A3 actually calls according to our exports.
"""

import json
from pathlib import Path

# Load function_bytes.json (our original export)
fb_path = Path('../ida_falconcd/function_bytes.json')
with open(fb_path) as f:
    func_bytes = json.load(f)

# Load segment_map.json  
sm_path = Path('segment_map.json')
with open(sm_path) as f:
    seg_map = json.load(f)

# Find sub_256A3 bytecode
sub_256A3_data = func_bytes.get('sub_256A3')
if not sub_256A3_data:
    print("sub_256A3 not found in function_bytes.json")
    exit(1)

# Convert hex string to bytes
bytes_hex = sub_256A3_data['bytes']
bytes_list = [int(bytes_hex[i:i+2], 16) for i in range(0, len(bytes_hex), 2)]
addr = sub_256A3_data['ea']

print("sub_256A3 Analysis")
print("=" * 70)
print(f"Address: 0x{addr:X}")
print(f"Size: {len(bytes_list)} bytes")
print(f"Bytecode: {' '.join(f'{b:02X}' for b in bytes_list)}")

# Look for CALL instructions (E8 xx xx for near call)

calls = []
for i, b in enumerate(bytes_list):
    if b == 0xE8:  # CALL near rel16
        if i + 2 < len(bytes_list):
            # Read 16-bit little-endian offset
            offset = bytes_list[i+1] + (bytes_list[i+2] << 8)
            # Sign-extend to 32-bit
            if offset & 0x8000:
                offset = offset - 0x10000
            # Calculate target (relative to NEXT instruction)
            next_inst = addr + i + 3
            target = next_inst + offset
            calls.append({
                'offset': i,
                'target': target,
                'rel_offset': offset
            })

print(f"\nCALL instructions found: {len(calls)}")
for call in calls:
    print(f"  +{call['offset']:02X}: CALL 0x{call['target']:04X} (rel {call['rel_offset']:+d})")
    
    # Try to find what function this is
    found = False
    for fname, fdata in func_bytes.items():
        if fdata['ea'] == call['target']:
            print(f"       -> {fname}")
            found = True
            break
    
    if not found:
        print(f"       -> NOT FOUND in function_bytes.json")
        
        # Check in segment_map
        for func in seg_map['functions']:
            if func['start_ea'] == call['target']:
                print(f"       -> Found in segment_map: {func['name']} at {func['segoff']}")
                break
        else:
            # Check if it's inside a function (multi-entry?)
            for func in seg_map['functions']:
                if func['start_ea'] <= call['target'] < func['end_ea']:
                    offset_in_func = call['target'] - func['start_ea']
                    print(f"       -> INSIDE {func['name']} at +0x{offset_in_func:04X}")
                    print(f"          Function: {func['segoff']} (0x{func['start_ea']:X} - 0x{func['end_ea']:X})")
                    break
            else:
                print(f"       -> Address 0x{call['target']:X} not found anywhere!")

print("\n" + "=" * 70)
print("Conclusion:")
print("=" * 70)
if calls:
    target_addr = calls[0]['target']
    print(f"sub_256A3 calls 0x{target_addr:X}")
    print(f"Expected: 0x10BDB (from earlier analysis)")
    print(f"Match: {'YES' if target_addr == 0x10BDB else 'NO'}")
else:
    print("No CALL instructions found in sub_256A3!")
