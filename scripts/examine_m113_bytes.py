import struct

obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
m113_obj = obj_data[offsets[36] : offsets[37]]

print("Raw bytes from 0x0060 to 0x00a0:")
for p in range(0x0060, 0x00a0, 2):
    b = m113_obj[p:p+2]
    w_u = struct.unpack('<H', b)[0]
    w_s = struct.unpack('<h', b)[0]
    print(f"0x{p:04x}: {b[0]:02x} {b[1]:02x} | unsigned={w_u:5d} (0x{w_u:04x}), signed={w_s:6d}")
