import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

vo = 102
for vi in [48, 49, 50, 51, 52, 53, 67, 68, 69, 70, 71, 72, 73]:
    v_off = vo + vi * 6
    raw = struct.unpack_from('<3h', f16, v_off)
    hex_raw = struct.unpack_from('<3H', f16, v_off)
    print(f"vi={vi:2d} (off={v_off:#06x}): raw={raw}  hex={[f'{h:#06x}' for h in hex_raw]}")
