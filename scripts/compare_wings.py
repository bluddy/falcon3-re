import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

f16 = data[offsets[3]:offsets[4]]
sig_pos = f16.find(b'\xFF\xFF\x00\x40')
lod_table_pos = sig_pos + 4
vc, vo, to, w3, w4 = struct.unpack_from('<5H', f16, lod_table_pos)

raw_verts = []
for vi in range(vc):
    x, y, z = struct.unpack_from('<hhh', f16, vo + vi * 6)
    # in Falcon coordinates: x=longitudinal (fwd), y=lateral (stbd), z=vertical (down)
    raw_verts.append((vi, x, y, z))

def print_face(name, idxs):
    print(f"\n--- {name}: {idxs} ---")
    for vi in idxs:
        v = raw_verts[vi]
        print(f"  v{vi:02d}: x={v[1]:5d}, y={v[2]:5d}, z={v[3]:5d} | GL: [x={v[2]/10.0:5.1f}, y={-v[3]/10.0:5.1f}, z={-v[1]/10.0:5.1f}]")

print("=== STARBOARD WING ===")
print_face("Face 20 (Main Wing)", [6, 30, 16, 17, 11, 8])
print_face("Face 24 (Flap)", [11, 10, 9, 8])
print_face("Face 30 (Inner Strake)", [43, 20, 17, 16])
print_face("Face 32 (Outer Strake)", [20, 19, 18, 17])

print("\n=== PORT WING ===")
print_face("Face 22 (Main Wing)", [7, 14, 15, 24, 25, 32])
print_face("Face 26 (Flap)", [15, 14, 13, 12])
print_face("Face 36 (Inner Strake)", [46, 25, 24, 23])
print_face("Face 34 (Outer Strake)", [23, 24, 22, 21])
