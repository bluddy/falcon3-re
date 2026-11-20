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
print(f"OBJECTS F16: vc={vc}, vo={vo} (0x{vo:04x}), to={to} (0x{to:04x})")

print(f"\nVertices at vo={vo} (0x{vo:04x}):")
verts = []
for i in range(min(10, vc)):
    v = struct.unpack_from('<hhh', obj, vo + i*6)
    print(f"  v[{i:2d}]: {v}")

print(f"\nLast 5 vertices at vo + (vc-5)*6:")
for i in range(vc - 5, vc):
    v = struct.unpack_from('<hhh', obj, vo + i*6)
    print(f"  v[{i:2d}]: {v}")
