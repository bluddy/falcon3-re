import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
o_f111 = data[offsets[8]:offsets[9]]

# Search for 10-byte LOD records: vc (10..200), vo (0..len), to (vo+vc*6..len), 0, 0
print(f"F-111 length: {len(o_f111)}")
for p in range(0x30, 0x200, 2):
    vc, vo, to, w3, w4 = struct.unpack_from('<5H', o_f111, p)
    if 20 <= vc <= 150 and 0x50 <= vo < len(o_f111) and vo + vc*6 <= len(o_f111) and vo + vc*6 <= to < len(o_f111) and w3 == 0 and w4 == 0:
        print(f"Found candidate LOD table at 0x{p:04x}: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}")
