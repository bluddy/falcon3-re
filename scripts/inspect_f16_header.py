import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

# Object 3 is F16
off = offsets[3]
next_off = offsets[4]
f16 = data[off:next_off]

print(f"F16 chunk size: {len(f16)} bytes")
print("First 64 bytes (hex):")
print(" ".join(f"{b:02x}" for b in f16[:64]))
print("First 32 words (hex):")
words = struct.unpack('<32H', f16[:64])
for i in range(0, 32, 8):
    print(f"{i:2d}: " + " ".join(f"{w:04x}" for w in words[i:i+8]))
