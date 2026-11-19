import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

for p in range(0x170, 0x1b0, 2):
    w = struct.unpack_from('<H', f16, p)[0]
    sw = struct.unpack_from('<h', f16, p)[0]
    print(f"{p:#06x}: {w:#06x} ({sw:6d})")
