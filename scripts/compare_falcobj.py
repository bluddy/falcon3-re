import struct

with open('game/FALCOBJ.BIN', 'rb') as f:
    d = f.read()

v_count, l_count = struct.unpack_from('<HH', d, 2)
print(f"FALCOBJ.BIN: v_count={v_count}, l_count={l_count}")

# Print first 20 vertices of FALCOBJ.BIN
v_start = 0xa0
print("\nFirst 25 vertices of FALCOBJ.BIN:")
for vi in range(25):
    x, y, z = struct.unpack_from('<hhh', d, v_start + vi*6)
    print(f"vi={vi:2d}: X={x:5d}, Y={y:5d}, Z={z:5d}")

# Check lines in FALCOBJ.BIN
l_start = v_start + v_count * 6
print(f"\nLines start at {l_start:#x}, total {l_count} lines")
for li in range(10):
    v1, v2 = struct.unpack_from('<hh', d, l_start + li*4)
    print(f"line {li:2d}: {v1} -> {v2}")
