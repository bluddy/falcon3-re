import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

print("Words from 0x66 to 0x120:")
for vi in range(20):
    v_off = 0x66 + vi * 6
    w = struct.unpack_from('<3h', f16, v_off)
    print(f"vi={vi:2d} (at {v_off:#06x}): {w}")
