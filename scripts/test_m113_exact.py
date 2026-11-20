import struct
import math

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])
m113 = data[offs[36]:offs[37]]

# Part 0 vertices at 0x0092 (14 verts)
raw_verts = [struct.unpack_from('<3h', m113, 0x0092 + i * 6) for i in range(14)]
gl_verts = [[round(v[0] / 10.0, 2), round(-v[1] / 10.0, 2), round(v[2] / 10.0, 2)] for v in raw_verts]

# Part 0 faces
# From 0x00e6, let's parse nodes
faces = []
unique = set()
for p in range(0x00e6, 0x0186, 2):
    if p + 8 <= len(m113):
        norm, mode, col, cnt = struct.unpack_from('<4H', m113, p)
        if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= 0x0186:
            v_words = struct.unpack_from(f'<{cnt+1}H', m113, p + 8)
            if all(w % 16 == 0 and (w // 16) < 14 for w in v_words) and v_words[0] == v_words[-1]:
                indices = [w // 16 for w in v_words[:-1]]
                key = tuple(sorted(indices))
                if key not in unique:
                    unique.add(key)
                    faces.append({'col': col, 'indices': indices})

print(f"Decoded {len(faces)} faces for Part 0:")
for f_idx, f in enumerate(faces):
    idx = f['indices']
    poly = [gl_verts[i] for i in idx]
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    cz = sum(p[2] for p in poly) / len(poly)
    v0, v1, v2 = poly[0], poly[1], poly[2]
    d1 = [v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]]
    d2 = [v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]]
    nx = d1[1]*d2[2] - d1[2]*d2[1]
    ny = d1[2]*d2[0] - d1[0]*d2[2]
    nz = d1[0]*d2[1] - d1[1]*d2[0]
    nlen = math.sqrt(nx*nx + ny*ny + nz*nz)
    un = (nx/nlen, ny/nlen, nz/nlen) if nlen > 1e-4 else (0, 0, 0)
    print(f"Face {f_idx:02d} (col {f['col']:3d}): indices={idx}")
    print(f"  Center: ({cx:6.2f}, {cy:6.2f}, {cz:6.2f}) | Normal: ({un[0]:5.2f}, {un[1]:5.2f}, {un[2]:5.2f})")
