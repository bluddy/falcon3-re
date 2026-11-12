import json
fb = json.load(open('../ida_falconcd/function_bytes.json'))

target = 0x10BDB

# Find which function contains this address
for fname, fdata in fb.items():
    fstart = fdata['ea']
    fsize = fdata['size']
    fend = fstart + fsize
    
    if fstart <= target < fend:
        offset = target - fstart
        print(f"0x{target:05X} is inside {fname}")
        print(f"  Function: 0x{fstart:05X} - 0x{fend:05X} ({fsize} bytes)")
        print(f"  Offset: +0x{offset:X} ({offset} bytes from start)")
        
        # Show bytecode around target
        bytecode = bytes.fromhex(fdata['bytes'])
        
        print(f"\n  Bytecode at offset +0x{offset:X}:")
        start_show = max(0, offset - 8)
        end_show = min(len(bytecode), offset + 16)
        
        for i in range(start_show, end_show, 16):
            hex_str = ' '.join(f"{bytecode[j]:02X}" for j in range(i, min(i+16, end_show)))
            marker = "    <-- HERE" if i <= offset < i+16 else ""
            print(f"    +0x{i:04X}: {hex_str}{marker}")
        
        break
else:
    print(f"0x{target:05X} is NOT inside any function!")
    print(f"\nThis means it's either:")
    print(f"  1. Unexplored bytes (not analyzed as code)")
    print(f"  2. Data between functions")
    print(f"  3. A boundary error (should be a function start)")
    
    # Check what's nearby
    nearby_before = max((f, d) for f, d in fb.items() if d['ea'] < target)
    nearby_after = min((f, d) for f, d in fb.items() if d['ea'] > target)
    
    print(f"\n  Function before: {nearby_before[0]} ends at 0x{nearby_before[1]['ea'] + nearby_before[1]['size']:05X}")
    print(f"  Gap: {target - (nearby_before[1]['ea'] + nearby_before[1]['size'])} bytes")
    print(f"  Function after: {nearby_after[0]} starts at 0x{nearby_after[1]['ea']:05X}")
    print(f"  Gap: {nearby_after[1]['ea'] - target} bytes")
