import json
fb = json.load(open('../ida_falconcd/function_bytes.json'))

# sub_256A3 calls "near 0x10BDB" - this is a RELATIVE call
# From 0x256A3, the call instruction is at offset 10 (after the DI setup)
# Call instruction: E8 2B B5
# This is: call rel16, where rel16 = 0xB52B (little endian)

# But wait, the disassembly says "call near 0x10BDB"
# Let me recalculate: the call is at 0x256AD (0x256A3 + 10)
# Call operand is 0xB52B
# Target = (0x256AD + 3) + 0xB52B = 0x256B0 + 0xB52B = 0x30BDB

# But that seems wrong too. Let me check if 0xB52B is signed
# 0xB52B as signed 16-bit = -19157 decimal
# So target = 0x256B0 + (-19157) = 0x256B0 - 0x4AD5 = 0x10BDB ✓

target_ea = 0x10BDB
print(f"Looking for function at 0x{target_ea:05X}...")

# Exact match
exact = [f for f, d in fb.items() if d['ea'] == target_ea]
if exact:
    print(f"FOUND: {exact}")
    for f in exact:
        print(f"  {f}: {fb[f]['size']} bytes")
        print(f"  Bytecode: {fb[f]['bytes'][:40]}...")
else:
    print(f"NOT FOUND at exact address")
    
    # Check nearby
    nearby = [(f, d) for f, d in fb.items() if 0x10BD0 <= d['ea'] <= 0x10BE5]
    nearby.sort(key=lambda x: x[1]['ea'])
    
    print(f"\nNearby functions:")
    for f, d in nearby:
        print(f"  {f}: 0x{d['ea']:05X} ({d['size']}B)")
    
    # Check if it's mid-body
    for f, d in fb.items():
        if d['ea'] < target_ea < d['ea'] + d['size']:
            offset = target_ea - d['ea']
            print(f"\n0x{target_ea:05X} is INSIDE {f} at offset +0x{offset:X}")
            print(f"  Function: 0x{d['ea']:05X} - 0x{d['ea'] + d['size']:05X}")
            break
