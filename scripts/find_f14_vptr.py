import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
o_f14 = data[offsets[0]:offsets[1]]

for p in range(0, 0x100, 2):
    w = struct.unpack_from('<H', o_f14, p)[0]
    if w in [0x1c8, 0x1ce, 0x1d0]:
        print(f"Reference to 0x{w:04x} at 0x{p:04x}")
