import struct

# OBJECTS M113
obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
m113_obj = obj_data[offsets[36] : offsets[37]]

print("=== Vertices at 0x0090 interpreted as signed shorts <hhh ===")
for i in range(14):
    x, y, z = struct.unpack_from('<hhh', m113_obj, 0x0090 + i * 6)
    print(f"  v{i:02d}: x={x:4d}, y={y:4d}, z={z:4d}")

# Let's check REPORT.DAT M113 vertices:
rep_data = open('game/REPORT.DAT', 'rb').read()
sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]
s_off = sec_offsets[2]
rel = struct.unpack_from('<I', rep_data, s_off + 2 + 4 * 4)[0]
m113_rep = rep_data[s_off + rel + 2 :]

print("\n=== REPORT.DAT M113 Vertices at 0x17b1 <hhh ===")
for i in range(14):
    x, y, z = struct.unpack_from('<hhh', m113_rep, 0x17b1 + i * 6)
    print(f"  v{i:02d}: x={x:4d}, y={y:4d}, z={z:4d}")
