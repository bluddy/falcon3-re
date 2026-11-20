import struct

obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
m113_obj = obj_data[offsets[36] : offsets[37]]

print("Words around 0x0080 - 0x00f0:")
for p in range(0x0080, 0x00f0, 2):
    w_signed = struct.unpack_from('<h', m113_obj, p)[0]
    w_unsigned = struct.unpack_from('<H', m113_obj, p)[0]
    print(f"0x{p:04x}: signed={w_signed:6d}, hex=0x{w_unsigned:04x}")
