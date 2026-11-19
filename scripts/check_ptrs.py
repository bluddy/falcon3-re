import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

ptrs = struct.unpack_from('<8H', f16, 0x224)
for i, p in enumerate(ptrs):
    words_around = struct.unpack_from('<8H', f16, p - 2 if p >= 2 else p)
    hexs = [f"{w:04x}" for w in words_around]
    print(f"Ptr {i} = {p:#06x}: words around: {' '.join(hexs)}")
