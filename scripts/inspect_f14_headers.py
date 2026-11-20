import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
o_f14 = data[offsets[0]:offsets[1]]

sig = o_f14.find(b'\xff\xff\x00\x40')
print(f"F-14 sig: 0x{sig:04x}")
for i in range(4):
    w5 = struct.unpack_from('<5H', o_f14, sig + 4 + i*10)
    print(f"  Header {i}: {[hex(x) for x in w5]}")
