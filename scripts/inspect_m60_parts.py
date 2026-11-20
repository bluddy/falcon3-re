import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[34] # M60
size = offsets[35] - off
obj = data[off:off+size]

print(f"M60 size={len(obj)}, words 0..40:")
words = [f"{w:04x}" for w in struct.unpack('<20H', obj[:40])]
print("0x00:", " ".join(words[:10]))
print("0x14:", " ".join(words[10:20]))

# Search for part pointers
for p in range(0x30, 0x100, 2):
    w = struct.unpack_from('<H', obj, p)[0]
    if 0x100 <= w < len(obj):
        # check if it looks like a part record
        w5 = struct.unpack_from('<5H', obj, w)
        if 2 <= w5[0] <= 60 and w5[1] < len(obj) and w5[2] < len(obj):
            print(f"Part record at offset 0x{w:04x} (ref from 0x{p:04x}): vc={w5[0]}, vo=0x{w5[1]:04x}, to=0x{w5[2]:04x}")
