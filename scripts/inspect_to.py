import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

print("Data at to=0x222 (octant table or node pointers?):")
words = struct.unpack_from("<32H", obj, 0x222)
for i, w in enumerate(words):
    print(f"  [{i:2d}] offset 0x{0x222 + i*2:04x}: {w} (0x{w:04x})")
