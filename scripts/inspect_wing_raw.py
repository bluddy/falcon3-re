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

for vi in range(16, 26):
    raw = f16[vo + vi*6 : vo + (vi+1)*6]
    x, y, z = struct.unpack_from('<hhh', raw)
    print(f"v{vi:02d}: x={x:4d} (0x{x&0xffff:04x}), y={y:4d} (0x{y&0xffff:04x}), z={z:4d} (0x{z&0xffff:04x}) raw={' '.join(f'{b:02x}' for b in raw)}")
