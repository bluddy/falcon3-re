import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

first_off = struct.unpack_from('<I', d, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', d[:first_off])

for obj_id in [3, 60]: # F16 vs FSX
    off = offsets[obj_id]
    next_off = offsets[obj_id+1]
    chunk = d[off:next_off]
    name = chunk[4:12].decode('ascii', errors='ignore').strip()
    sig = chunk.find(b'\xff\xff\x00\x40')
    vc, vo, to = struct.unpack_from('<3H', chunk, sig + 4)
    print(f"\nObject {obj_id} ({name}): vc={vc}, vo={vo:#x}, to={to:#x}")
    # Search for color 178
    pos = 0
    while True:
        idx = chunk.find(b'\xb2\x00', pos)
        if idx == -1: break
        cnt = struct.unpack_from('<H', chunk, idx + 2)[0]
        if 3 <= cnt <= 8:
            v_words = struct.unpack_from(f'<{cnt+1}H', chunk, idx + 4)
            indices = [w // 16 for w in v_words]
            print(f"  Color 178 face at {idx:#x}: cnt={cnt}, indices={indices}")
            for vi in indices[:-1]:
                v_off = vo + vi * 6
                x, y, z = struct.unpack_from('<3h', chunk, v_off)
                print(f"     vi={vi:2d}: X={x:5d}, Y={y:5d}, Z={z:5d}")
        pos = idx + 1
