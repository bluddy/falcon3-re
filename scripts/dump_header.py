import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

for addr in range(0x220, 0x240, 2):
    w = struct.unpack_from('<H', f16, addr)[0]
    print(f"{addr:#06x}: {w:#06x} ({w:5d})")
