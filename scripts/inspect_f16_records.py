import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

ptrs = [0x222, 0x232, 0x288, 0x2de, 0x330, 0x382, 0x3ce, 0x41a, 0x466, 0x4c6]
for ptr in ptrs:
    sub = f16[ptr:ptr+32]
    words = [f'{w:04x}' for w in struct.unpack(f'<{len(sub)//2}H', sub)]
    print(f'Offset {ptr:#06x} ({ptr:4d}): {" ".join(words)}')
