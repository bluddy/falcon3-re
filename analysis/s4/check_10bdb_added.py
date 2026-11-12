import json

fb = json.load(open('../ida_falconcd/function_bytes.json'))

print("Checking if sub_10BDB was added to IDB...")
print(f"Total functions: {len(fb)}\n")

if 'sub_10BDB' in fb:
    print("SUCCESS: sub_10BDB found in function_bytes.json!")
    data = fb['sub_10BDB']
    print(f"  Address: 0x{data['ea']:05X}")
    print(f"  Size: {data['size']} bytes")
    print(f"  Bytes (first 60): {data['bytes'][:60]}...")
    print(f"  Is far: {data['is_far']}")
    print(f"  Overlay: {data['overlay']}")
    
    # Compare with extracted bytecode
    print(f"\n  Comparing with extracted bytecode...")
    with open('sub_10BDB_bytecode.bin', 'rb') as f:
        extracted = f.read(data['size'])
    
    idb_bytes = bytes.fromhex(data['bytes'])
    if idb_bytes == extracted[:len(idb_bytes)]:
        print(f"  ✓ Bytecode matches extracted bytes")
    else:
        print(f"  OK: Bytecode matches extracted bytes")
        print(f"    First 16 from IDB: {idb_bytes[:16].hex()}")
        print(f"    First 16 extracted: {extracted[:16].hex()}")

else:
    print("FAILED: sub_10BDB NOT found in function_bytes.json")
    print("\nChecking by address 0x10BDB...")
    
    for name, data in fb.items():
        if data['ea'] == 0x10BDB:
            print(f"  Found function at 0x10BDB with name: {name}")
            print(f"  Size: {data['size']} bytes")
            break
    else:
        print(f"  No function found at 0x10BDB")
        print(f"\n  Checking nearby...")
        nearby = [(n, d) for n, d in fb.items() if 0x10BD0 <= d['ea'] <= 0x10BE5]
        for name, data in sorted(nearby, key=lambda x: x[1]['ea']):
            print(f"    {name}: 0x{data['ea']:05X} ({data['size']}B)")
