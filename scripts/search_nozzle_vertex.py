import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

# Let's search for (Y=0, Z=13) or (Y=0, Z=-13) or (Y=0, Z=130) across all vertices of all objects
first_off = struct.unpack_from('<I', d, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', d[:first_off])

print("Searching for nozzle bottom vertex across all objects:")
for i in range(num_objs):
    off = offsets[i]
    next_off = offsets[i+1] if i+1 < num_objs else len(d)
    chunk = d[off:next_off]
    name = chunk[4:12].decode('ascii', errors='ignore').strip()
    sig = chunk.find(b'\xff\xff\x00\x40')
    if sig != -1:
        vc, vo, to = struct.unpack_from('<3H', chunk, sig + 4)
        for vi in range(vc):
            v_off = vo + vi * 6
            if v_off + 6 <= len(chunk):
                x, y, z = struct.unpack_from('<3h', chunk, v_off)
                if y == 0 and abs(z) in [12, 13, 14, 15, 16]:
                    print(f"Obj {i} ({name}) v{vi}: X={x}, Y={y}, Z={z}")
