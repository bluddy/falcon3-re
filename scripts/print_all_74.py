import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

print("All 74 vertices in F-16 (raw X, Y, Z in file):")
for vi in range(74):
    v_off = 0x66 + vi * 6
    x, y, z = struct.unpack_from('<3h', f16, v_off)
    print(f"vi={vi:2d} (at {v_off:#06x}): X={x:5d}, Y={y:5d}, Z={z:5d}")
