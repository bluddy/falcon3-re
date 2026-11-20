import struct

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])

# F-16: Obj 3
f16 = data[offs[3]:offs[4]]
raw_verts = [struct.unpack_from('<3h', f16, 0x0066 + i * 6) for i in range(74)]

# Let's inspect the vertical fin and cockpit faces in F-16
# Nodes start at 0x0222
faces = []
for p in range(0x0222, 0x0874, 2):
    if p + 8 <= len(f16):
        norm, mode, col, cnt = struct.unpack_from('<4H', f16, p)
        if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= 0x0874:
            v_words = struct.unpack_from(f'<{cnt+1}H', f16, p + 8)
            if all(w % 16 == 0 and (w // 16) < 74 for w in v_words) and v_words[0] == v_words[-1]:
                indices = [w // 16 for w in v_words[:-1]]
                faces.append((col, indices))

print(f"Decoded {len(faces)} faces for F-16 LOD 0")
# Let's check canopy/cockpit (usually col 140 or similar, or top vertices)
# In raw_verts:
# v[0] is forward (X: -110 to +200)
# v[1] is right (Y: -120 to +120)
# v[2] is up/down (Z: -20 to +50?)
zs = [v[2] for v in raw_verts]
print(f"Z range in F-16 raw verts: min={min(zs)}, max={max(zs)}")

# Which vertices have max Z?
max_z_verts = [(i, raw_verts[i]) for i in range(len(raw_verts)) if raw_verts[i][2] > 20]
print(f"Vertices with high Z (>20): {max_z_verts}")
