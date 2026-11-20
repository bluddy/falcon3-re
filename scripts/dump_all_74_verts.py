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

print(f"=== ALL {vc} VERTICES OF F-16 CHUNK 3 ===")
for vi in range(vc):
    x, y, z = struct.unpack_from('<hhh', f16, vo + vi * 6)
    print(f"v{vi:02d}: x={x:5d}, y={y:5d}, z={z:5d}  (hex: {x&0xffff:04x}, {y&0xffff:04x}, {z&0xffff:04x})")
