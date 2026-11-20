import struct

# REPORT.DAT M113
rep_data = open('game/REPORT.DAT', 'rb').read()
sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]
s_off = sec_offsets[2]
rel = struct.unpack_from('<I', rep_data, s_off + 2 + 4 * 4)[0]
m113_rep = rep_data[s_off + rel + 2 :]

# OBJECTS M113
obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
m113_obj = obj_data[offsets[36] : offsets[37]]

print("=== PART 0 (Hull) Vertices ===")
print("REPORT.DAT (from 0x17b1, vc=14):")
for i in range(14):
    v = struct.unpack_from('<hhh', m113_rep, 0x17b1 + i * 6)
    print(f"  v{i:02d}: x={v[0]:5d}, y={v[1]:5d}, z={v[2]:5d}")

print("\nOBJECTS (from 0x0090, vc=14):")
for i in range(14):
    v = struct.unpack_from('<hhh', m113_obj, 0x0090 + i * 6)
    print(f"  v{i:02d}: x={v[0]:5d}, y={v[1]:5d}, z={v[2]:5d}")

print("\n=== PART 1 Vertices ===")
print("REPORT.DAT (from 0x1a37, vc=4):")
for i in range(4):
    v = struct.unpack_from('<hhh', m113_rep, 0x1a37 + i * 6)
    print(f"  v{i:02d}: x={v[0]:5d}, y={v[1]:5d}, z={v[2]:5d}")

print("\nOBJECTS (from 0x048a, vc=4):")
for i in range(4):
    v = struct.unpack_from('<hhh', m113_obj, 0x048a + i * 6)
    print(f"  v{i:02d}: x={v[0]:5d}, y={v[1]:5d}, z={v[2]:5d}")

print("\n=== PART 2 Vertices ===")
print("REPORT.DAT (from 0x1b63, vc=2):")
for i in range(2):
    v = struct.unpack_from('<hhh', m113_rep, 0x1b63 + i * 6)
    print(f"  v{i:02d}: x={v[0]:5d}, y={v[1]:5d}, z={v[2]:5d}")

print("\nOBJECTS (from 0x05b6, vc=2):")
for i in range(2):
    v = struct.unpack_from('<hhh', m113_obj, 0x05b6 + i * 6)
    print(f"  v{i:02d}: x={v[0]:5d}, y={v[1]:5d}, z={v[2]:5d}")
