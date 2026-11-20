import struct

with open('game/OBJECTS', 'rb') as f:
    d_obj = f.read()

first_off = struct.unpack_from('<I', d_obj, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', d_obj[:first_off])
o_f16 = d_obj[offsets[3]:offsets[4]]

vc, vo, to = struct.unpack_from('<3H', o_f16, 0x40)
raw_verts = [struct.unpack_from('<hhh', o_f16, vo + i*6) for i in range(vc)]

print("First 15 raw vertices of F-16 in OBJECTS (X, Y, Z):")
for i, (x, y, z) in enumerate(raw_verts[:15]):
    print(f"  v{i:2d}: X={x:5d}, Y={y:5d}, Z={z:5d}")

# Check min and max along X, Y, Z
xs = [v[0] for v in raw_verts]
ys = [v[1] for v in raw_verts]
zs = [v[2] for v in raw_verts]
print(f"\nRanges in OBJECTS:")
print(f"  X: min={min(xs)}, max={max(xs)}, span={max(xs)-min(xs)}")
print(f"  Y: min={min(ys)}, max={max(ys)}, span={max(ys)-min(ys)}")
print(f"  Z: min={min(zs)}, max={max(zs)}, span={max(zs)-min(zs)}")
