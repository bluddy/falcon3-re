import struct

with open('game/OBJECTS', 'rb') as f:
    d = f.read()

off = struct.unpack_from('<I', d, 12)[0]
f16 = d[off:off+3124]

sig = f16.find(b'\xff\xff\x00\x40')
vc, vo, to = struct.unpack_from('<3H', f16, sig + 4)

verts = []
for vi in range(vc):
    x, y, z = struct.unpack_from('<3h', f16, vo + vi*6)
    verts.append((x, y, z))

# Identify wing vertices (abs(Y) >= 45)
wing_verts = {vi for vi, (x, y, z) in enumerate(verts) if abs(y) >= 45}
print("Wing vertices (abs(Y) >= 45):", wing_verts)
for vi in sorted(wing_verts):
    print(f"  v{vi:2d}: {verts[vi]}")

# Let's inspect all polygon records in LOD 0 (to = 0x222 .. 0x874)
# Check every record that touches any wing vertex
p = 0x4c6
while p + 8 <= 0x874:
    col, cnt = struct.unpack_from('<2H', f16, p)
    if 1 <= col <= 255 and 3 <= cnt <= 8:
        v_words = struct.unpack_from(f'<{cnt+1}H', f16, p + 4)
        if all(w % 16 == 0 and w // 16 < vc for w in v_words):
            ring = [w // 16 for w in v_words]
            if any(vi in wing_verts for vi in ring):
                print(f"\nPoly at {p:#06x}: col={col}, ring={ring}")
                for vi in ring:
                    print(f"    v{vi:2d}: {verts[vi]}")
            p += (cnt + 4) * 2
            continue
    p += 2
