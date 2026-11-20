import struct
import math

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])
m113 = data[offs[36]:offs[37]]

# Part 0: Hull (14 verts at 0x0092)
p0_verts = [struct.unpack_from('<3h', m113, 0x0092 + i * 6) for i in range(14)]
# Part 1: Cupola (4 verts at 0x0188)
p1_verts = [struct.unpack_from('<3h', m113, 0x0188 + i * 6) for i in range(4)]
# Part 2: Gun barrel (2 verts at 0x01d2)
p2_verts = [struct.unpack_from('<3h', m113, 0x01d2 + i * 6) for i in range(2)]

raw_all = p0_verts + p1_verts + p2_verts
gl_all = [[round(v[0] / 10.0, 2), round(-v[1] / 10.0, 2), round(v[2] / 10.0, 2)] for v in raw_all]

print(f"Total verts: {len(gl_all)}")
for i, v in enumerate(gl_all):
    print(f"  v{i:02d}: {v}")

# Decode Part 1 faces (from 0x019e to 0x01d0)
p1_faces = []
for p in range(0x019e, 0x01d0, 2):
    if p + 8 <= len(m113):
        norm, mode, col, cnt = struct.unpack_from('<4H', m113, p)
        if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= 0x01d0:
            v_words = struct.unpack_from(f'<{cnt+1}H', m113, p + 8)
            if all(w % 16 == 0 and (w // 16) < 4 for w in v_words) and v_words[0] == v_words[-1]:
                indices = [w // 16 + 14 for w in v_words[:-1]]
                p1_faces.append({'col': col, 'indices': indices})

print(f"\nPart 1 faces: {len(p1_faces)}")
for f in p1_faces:
    print(f"  indices={f['indices']}, col={f['col']}")

# In REPORT.DAT:
# Part 1 faces:
# f08: indices=[17, 16, 14], col=118
# f09: indices=[14, 15, 17], col=121
# f10: indices=[17, 15, 16], col=119
