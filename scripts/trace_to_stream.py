import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
obj = data[offsets[3]:offsets[4]] # F-16 in OBJECTS

sig = obj.find(b'\xff\xff\x00\x40')
vc, vo, to = struct.unpack_from('<3H', obj, sig + 4)
print(f"F-16: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}")

p = to
to_entries = []
while p + 2 <= len(obj):
    w = struct.unpack_from('<H', obj, p)[0]
    p += 2
    if w == 0xFFFF:
        print(f"Encountered 0xFFFF at offset 0x{p-2:04x}!")
        break
    to_entries.append((p-2, w))

print(f"Total entries in to stream before 0xFFFF: {len(to_entries)}")
for off, w in to_entries:
    print(f"  Entry at 0x{off:04x}: ptr=0x{w:04x}")
