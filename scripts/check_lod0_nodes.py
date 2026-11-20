import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

vc, vo, to = struct.unpack_from('<3H', obj, 0x40)

# Scan from 0x04c6 to 0x0874
lod0_nodes = []
for p in range(0x4c0, 0x874, 2):
    norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
    if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= len(obj):
        v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
        if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
            if v_words[0] == v_words[-1]:
                lod0_nodes.append((p, col & 0xFF, cnt, [w // 16 for w in v_words[:-1]]))

print(f"Total nodes in LOD 0 range (0x4c0..0x874): {len(lod0_nodes)}")

# Check unique faces
unique_faces = {}
for p, col, cnt, ring in lod0_nodes:
    k = tuple(sorted(ring))
    if k not in unique_faces:
        unique_faces[k] = (p, col, ring)

print(f"Total unique faces in LOD 0: {len(unique_faces)}")
