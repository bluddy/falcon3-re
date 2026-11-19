import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

# Let's inspect the first 120 bytes of F16
print("F16 header:")
for i in range(0, 120, 16):
    chunk = f16[i:i+16]
    hex_str = ' '.join(f'{b:02x}' for b in chunk)
    print(f"{i:#06x}: {hex_str}")
