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
raw_verts = [struct.unpack_from('<hhh', obj, vo + i*6) for i in range(vc)]

# Let's inspect all vertices with Y != 0:
left_verts = [(i, v) for i, v in enumerate(raw_verts) if v[1] < 0]
right_verts = [(i, v) for i, v in enumerate(raw_verts) if v[1] > 0]
center_verts = [(i, v) for i, v in enumerate(raw_verts) if v[1] == 0]

print(f"Center vertices (Y=0): {len(center_verts)}")
for i, v in center_verts:
    print(f"  v{i:02d}: {v}")

print(f"\nLeft vertices (Y < 0): {len(left_verts)}")
for i, v in left_verts:
    print(f"  v{i:02d}: {v}")

print(f"\nRight vertices (Y > 0): {len(right_verts)}")
for i, v in right_verts:
    print(f"  v{i:02d}: {v}")
