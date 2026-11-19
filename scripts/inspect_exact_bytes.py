import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

for addr in range(0x50, 0x80):
    print(f"{addr:#04x}: {f16[addr]:02x} ({f16[addr]:3d})")
