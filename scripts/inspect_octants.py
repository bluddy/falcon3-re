import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

print("Words at 0x21c..0x238:")
for p in range(0x21c, 0x238, 2):
    w = struct.unpack_from("<H", obj, p)[0]
    print(f"  0x{p:04x}: {w} (0x{w:04x})")

print("\nWhat is at 0x0232:")
print(f"  0x0232: {[hex(w) for w in struct.unpack_from('<12H', obj, 0x0232)]}")
