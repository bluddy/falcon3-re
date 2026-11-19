import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

# Let's inspect LOD 1 at 2164 (0x874)
chunk = f16[2164:2164+64]
words = [f'{w:04x}' for w in struct.unpack(f'<{len(chunk)//2}H', chunk)]
print("LOD 1 at 0x874:")
print(' '.join(words))

# Let's inspect LOD 2 at 2970 (0xb9a)
chunk2 = f16[2970:2970+64]
words2 = [f'{w:04x}' for w in struct.unpack(f'<{len(chunk2)//2}H', chunk2)]
print("LOD 2 at 0xb9a:")
print(' '.join(words2))
