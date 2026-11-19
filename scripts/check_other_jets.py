import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

first_off = struct.unpack_from('<I', d, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', d[:first_off])

for obj_id in [0, 2, 3, 4]: # F14, F15, F16, FA18
    off = offsets[obj_id]
    next_off = offsets[obj_id+1]
    chunk = d[off:next_off]
    name = chunk[4:12].decode('ascii', errors='ignore').strip()
    sig = chunk.find(b'\xff\xff\x00\x40')
    vc, vo, to = struct.unpack_from('<3H', chunk, sig + 4)
    print(f"\nObject {obj_id} ({name}): vc={vc}, vo={vo:#x}, to={to:#x}")
    # Search for color 178 (0x00b2)
    pos = 0
    while True:
        idx = chunk.find(b'\xb2\x00', pos)
        if idx == -1: break
        # check if word before or after is vertex count
        cnt = struct.unpack_from('<H', chunk, idx + 2)[0]
        if 3 <= cnt <= 8:
            v_words = struct.unpack_from(f'<{cnt+1}H', chunk, idx + 4)
            indices = [w // 16 for w in v_words]
            print(f"  Color 178 face at {idx:#x}: cnt={cnt}, words={v_words}, indices={indices}")
        pos = idx + 1
