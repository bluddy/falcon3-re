import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

# Check header around 0x3c
print("Header around 0x30..0x66:")
for i in range(0x30, 0x66, 2):
    w = struct.unpack_from("<H", obj, i)[0]
    print(f"  0x{i:02x}: {w} (0x{w:04x})")

print("\nWhat is at 0x00b4 (word 0 of to)?")
print(f"  0x00b4: {[hex(w) for w in struct.unpack_from('<8H', obj, 0x00b4)]}")

print("\nWhat is at 0x0288 (word 2 of to)?")
print(f"  0x0288: {[hex(w) for w in struct.unpack_from('<12H', obj, 0x0288)]}")

print("\nWhat is at 0x04d6 (first pointer in 0x0288)?")
print(f"  0x04d6: {[hex(w) for w in struct.unpack_from('<12H', obj, 0x04d6)]}")
