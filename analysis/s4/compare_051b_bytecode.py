#!/usr/bin/env python3
"""Compare bytes at seg020:051B with extracted sub_10BDB bytecode"""
import json

fb = json.load(open('../ida_falconcd/function_bytes.json'))

# Get record_xform_apply
if 'record_xform_apply' not in fb:
    print("ERROR: record_xform_apply not found!")
    exit(1)

rxf = fb['record_xform_apply']
print(f"record_xform_apply:")
print(f"  Address: 0x{rxf['ea']:05X}")
print(f"  Size: {rxf['size']} bytes")

# Calculate linear address of seg020:051B
# We know seg020:5FED = 0x256A3
# So seg020 base = 0x256A3 - 0x5FED = 0x1F6B6
seg020_base = 0x1F6B6
offset_051b = 0x051B
linear_051b = seg020_base + offset_051b

print(f"\nseg020:051B:")
print(f"  Linear address: 0x{linear_051b:05X}")

# Calculate offset within record_xform_apply
if linear_051b >= rxf['ea'] and linear_051b < rxf['ea'] + rxf['size']:
    offset_in_func = linear_051b - rxf['ea']
    print(f"  Offset in record_xform_apply: +0x{offset_in_func:X} ({offset_in_func} bytes)")
    
    # Extract bytes from IDB at this offset
    hex_bytes = rxf['bytes']
    start_pos = offset_in_func * 2  # 2 hex chars per byte
    idb_bytes_hex = hex_bytes[start_pos:start_pos + 64]
    idb_bytes = bytes.fromhex(idb_bytes_hex)
    
    print(f"\n  Bytes from IDB at seg020:051B:")
    print(f"    {idb_bytes.hex()}")
    
    # Load extracted bytecode
    try:
        with open('sub_10BDB_bytecode.bin', 'rb') as f:
            extracted = f.read(32)
        
        print(f"\n  Extracted sub_10BDB bytecode:")
        print(f"    {extracted.hex()}")
        
        # Compare
        if idb_bytes[:32] == extracted:
            print(f"\n  [MATCH] Bytes match perfectly!")
            print(f"\n  CONCLUSION: seg020:051B IS the code we're looking for")
            print(f"  It's currently part of record_xform_apply as a secondary entry point")
        else:
            print(f"\n  [MISMATCH] Bytes don't match")
            print(f"  First difference at byte {next((i for i in range(32) if idb_bytes[i] != extracted[i]), 32)}")
    
    except FileNotFoundError:
        print(f"\n  sub_10BDB_bytecode.bin not found, cannot compare")

else:
    print(f"  ERROR: 0x{linear_051b:05X} is NOT inside record_xform_apply")
    print(f"  record_xform_apply spans: 0x{rxf['ea']:05X} - 0x{rxf['ea']+rxf['size']:05X}")
