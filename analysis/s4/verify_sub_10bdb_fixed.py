#!/usr/bin/env python3
"""
Verify that sub_10BDB was successfully added to IDB.
Run this after manual IDA addition.
"""
import json
from pathlib import Path

print("="*80)
print("VERIFICATION: sub_10BDB Addition")
print("="*80)

# Load function_bytes.json
fb_path = Path("../ida_falconcd/function_bytes.json")
if not fb_path.exists():
    print("\nERROR: function_bytes.json not found!")
    print(f"Expected at: {fb_path.absolute()}")
    exit(1)

fb = json.load(open(fb_path))

print(f"\nTotal functions in IDB: {len(fb)}")
print(f"Expected: 4,128 (was 4,127 + 1)")

# Check if sub_10BDB exists
if 'sub_10BDB' in fb:
    print("\n[SUCCESS] sub_10BDB found in function_bytes.json!")
    
    data = fb['sub_10BDB']
    print(f"\n  Address: 0x{data['ea']:05X}")
    print(f"  Size: {data['size']} bytes")
    print(f"  Is far: {data['is_far']}")
    print(f"  Overlay: {data['overlay']}")
    
    # Show first bytes
    bytecode = data['bytes']
    print(f"\n  Bytecode (first 32 bytes):")
    for i in range(0, min(64, len(bytecode)), 32):
        print(f"    {bytecode[i:i+32]}")
    
    # Compare with extracted bytecode
    extracted_path = Path("sub_10BDB_bytecode.bin")
    if extracted_path.exists():
        print(f"\n  Comparing with extracted bytecode...")
        with open(extracted_path, 'rb') as f:
            extracted = f.read(data['size'])
        
        idb_bytes = bytes.fromhex(data['bytes'])
        if idb_bytes == extracted[:len(idb_bytes)]:
            print(f"  [OK] Bytecode matches extracted bytes")
        else:
            print(f"  [WARNING] Bytecode mismatch!")
            print(f"    IDB starts: {idb_bytes[:16].hex()}")
            print(f"    Extracted:  {extracted[:16].hex()}")
    
    # Check caller (sub_256A3)
    print(f"\n  Checking caller sub_256A3...")
    if 'sub_256A3' in fb:
        caller_data = fb['sub_256A3']
        print(f"    sub_256A3 exists at 0x{caller_data['ea']:05X}")
        print(f"    Size: {caller_data['size']} bytes")
        
        # The call should be at offset +10 in sub_256A3
        # Bytecode: E8 2B B5 (call near -19157)
        caller_bytes = bytes.fromhex(caller_data['bytes'])
        if len(caller_bytes) >= 13:
            call_bytes = caller_bytes[10:13]  # Offset +10
            if call_bytes[0] == 0xE8:  # Call near
                rel_offset = int.from_bytes(call_bytes[1:3], 'little', signed=True)
                call_target = caller_data['ea'] + 13 + rel_offset  # +13 = after call instruction
                
                print(f"    Call instruction at +10: E8 {call_bytes[1]:02X} {call_bytes[2]:02X}")
                print(f"    Relative offset: {rel_offset}")
                print(f"    Target address: 0x{call_target:05X}")
                
                if call_target == data['ea']:
                    print(f"    [OK] sub_256A3 correctly calls sub_10BDB")
                else:
                    print(f"    [WARNING] Call target mismatch!")
                    print(f"      Expected: 0x{data['ea']:05X}")
                    print(f"      Got: 0x{call_target:05X}")
            else:
                print(f"    [WARNING] Expected call instruction (E8) at offset +10")
                print(f"      Got: {call_bytes.hex()}")
    else:
        print(f"    [WARNING] sub_256A3 not found in function_bytes")
    
    print("\n" + "="*80)
    print("VERIFICATION PASSED")
    print("="*80)
    print("\nNext steps:")
    print("  1. Analyze sub_10BDB disassembly in IDA")
    print("  2. Understand DGROUP:0x4287 access pattern")
    print("  3. Name the function appropriately")
    print("  4. Document findings")
    
    exit(0)

else:
    print("\n[FAILED] sub_10BDB NOT found in function_bytes.json")
    
    # Check by address
    print("\nSearching by address 0x10BDB...")
    found_by_addr = False
    for name, data in fb.items():
        if data['ea'] == 0x10BDB:
            print(f"  Found function at 0x10BDB with name: {name}")
            print(f"  Size: {data['size']} bytes")
            found_by_addr = True
            break
    
    if not found_by_addr:
        print(f"  No function found at address 0x10BDB")
        
        # Check gap
        print(f"\n  Checking gap (0x10B40 - 0x10BE0)...")
        in_gap = [(n, d) for n, d in fb.items() if 0x10B40 <= d['ea'] <= 0x10BE0]
        
        if in_gap:
            print(f"  Functions in gap region:")
            for name, data in sorted(in_gap, key=lambda x: x[1]['ea']):
                print(f"    {name}: 0x{data['ea']:05X} ({data['size']}B)")
        else:
            print(f"  No functions in gap region")
        
        print("\n" + "="*80)
        print("VERIFICATION FAILED")
        print("="*80)
        print("\nPossible reasons:")
        print("  1. Function not created in IDA")
        print("  2. Function created with different name")
        print("  3. function_bytes.json not re-exported")
        print("\nRefer to: docs/manual_add_sub_10bdb.md")
    
    exit(1)
