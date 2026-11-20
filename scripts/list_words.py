import struct

obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
m113_obj = obj_data[offsets[36] : offsets[37]]

print("All words in m113_obj from 0x0070 to 0x0100:")
for p in range(0x0070, 0x0100, 2):
    w_s = struct.unpack_from('<h', m113_obj, p)[0]
    w_u = struct.unpack_from('<H', m113_obj, p)[0]
    print(f"0x{p:04x} (+{p-0x90:3d}): {w_s:6d} (0x{w_u:04x})")
