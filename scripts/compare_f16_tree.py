import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
obj = data[offsets[3]:offsets[4]] # F-16 in OBJECTS

sig = obj.find(b'\xff\xff\x00\x40')
print(f"F-16 sig: 0x{sig:04x}")
vc, vo, to = struct.unpack_from('<3H', obj, sig + 4)
print(f"LOD 0: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}")

# Let's inspect words at 'to':
to_words = [f"0x{w:04x}" for w in struct.unpack('<16H', obj[to:to+32])]
print(f"Words at to (0x{to:04x}): {to_words}")
