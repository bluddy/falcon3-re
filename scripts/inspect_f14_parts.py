import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
o_f14 = data[offsets[0]:offsets[1]]

for p in range(0x190, 0x220, 16):
    words = [hex(w) for w in struct.unpack('<8H', o_f14[p:p+16])]
    print(f"0x{p:04x}: {words}")
