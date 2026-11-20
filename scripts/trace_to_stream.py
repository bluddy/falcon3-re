import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

vc, vo, to = struct.unpack_from('<3H', obj, 0x40)
print(f"OBJECTS F16: vc={vc}, vo={vo} (0x{vo:04x}), to={to} (0x{to:04x})")

# Let's inspect the exact pointers starting at to (0x0222)
p = to
while p + 2 <= len(obj):
    w = struct.unpack_from('<H', obj, p)[0]
    p += 2
    if w == 0xFFFF:
        print(f"Reached 0xFFFF at offset 0x{p-2:04x}")
        break
    print(f"Pointer at 0x{p-2:04x}: 0x{w:04x} ({w})")
