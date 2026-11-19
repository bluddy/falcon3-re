import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

# Read the header at 0x222
w0 = struct.unpack_from('<H', f16, 0x222)[0]
print(f"Header at 0x222: {w0:#06x} ({w0})")

# Read pointers
ptrs = struct.unpack_from('<8H', f16, 0x224)
print("Display list pointers:", [f"{p:#06x}" for p in ptrs])

for idx, p in enumerate(ptrs):
    # Read until 0xffff
    curr = p
    poly_ptrs = []
    while curr + 2 <= len(f16):
        val = struct.unpack_from('<H', f16, curr)[0]
        if val == 0xFFFF:
            break
        poly_ptrs.append(val)
        curr += 2
    print(f"List {idx} (at {p:#06x}): {len(poly_ptrs)} polygons -> {[f'{x:#06x}' for x in poly_ptrs[:8]]}...")
