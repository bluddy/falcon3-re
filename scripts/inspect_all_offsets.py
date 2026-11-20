import struct

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])

for obj_idx in [0, 1, 2, 3, 34, 35, 36, 67]:
    obj = data[offs[obj_idx] : (offs[obj_idx+1] if obj_idx+1 < len(offs) else len(data))]
    name = obj[4:12].decode('latin1', errors='replace').strip()
    byte2 = struct.unpack_from('<H', obj, 2)[0]
    print(f"\n--- Obj {obj_idx:02d} ({name}), byte2=0x{byte2:04x}, len={len(obj)} ---")
    # In M113, byte2 is 0x010a
    # Let's inspect bytes 0x000c to 0x0070
    lod_ptr = struct.unpack_from('<H', obj, 0x10)[0] if len(obj) > 0x12 else 0
    print(f"  Word at 0x10: 0x{lod_ptr:04x} ({lod_ptr})")
    if lod_ptr < len(obj):
        for k in range(lod_ptr, min(lod_ptr + 20, len(obj)), 2):
            w = struct.unpack_from('<H', obj, k)[0]
            print(f"    +0x{k-lod_ptr:02x} (0x{k:04x}): 0x{w:04x} ({w})")
