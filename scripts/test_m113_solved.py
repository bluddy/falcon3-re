import struct
from PIL import Image, ImageDraw
import math

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])
m113 = data[offs[36]:offs[37]]

# Parse 3 parts of M113
parts = [
    # (vc, vo, to, trans_ptr)
    (14, 0x0090 + 2, 0x00e6, 0x007e),
    ( 4, 0x0186 + 2, 0x019e, 0x0084),
    ( 2, 0x01d0 + 2, 0x01dc, 0x008a),
]

all_verts = []
all_faces = []
v_base = 0

for vc, vo, to, trans_ptr in parts:
    tx, ty, tz = struct.unpack_from('<3h', m113, trans_ptr) if trans_ptr else (0, 0, 0)
    raw_verts = [struct.unpack_from('<3h', m113, vo + i * 6) for i in range(vc)]
    # Apply translation
    for rx, ry, rz in raw_verts:
        # GL transform: X = rx + tx, Y = -(ry + ty), Z = rz + tz
        all_verts.append([
            round((rx + tx) / 10.0, 2),
            round(-(ry + ty) / 10.0, 2),
            round((rz + tz) / 10.0, 2)
        ])
    
    # Parse nodes for this part
    # Scan from to until next part vo or 0x01ea (end of LOD 0)
    p_end = 0x01ea
    unique = set()
    for p in range(to, p_end, 2):
        if p + 8 <= len(m113):
            norm, mode, col, cnt = struct.unpack_from('<4H', m113, p)
            if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= p_end:
                v_words = struct.unpack_from(f'<{cnt+1}H', m113, p + 8)
                if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                    indices = [w // 16 + v_base for w in v_words[:-1]]
                    key = tuple(sorted(indices))
                    if key not in unique:
                        unique.add(key)
                        all_faces.append({'col': col, 'indices': indices})
    v_base += vc

print(f"Total M113 verts: {len(all_verts)}, faces: {len(all_faces)}")
for i, f in enumerate(all_faces):
    print(f"  Face {i:02d} (col {f['col']}): indices={f['indices']}")

# Now render turnaround of M113
def project(v, yaw, pitch, scale=18.0, cx=150, cy=150):
    x, y, z = v
    rad_y = math.radians(yaw)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    x1 = x * cos_y + z * sin_y
    z1 = -x * sin_y + z * cos_y
    rad_p = math.radians(pitch)
    cos_p, sin_p = math.cos(rad_p), math.sin(rad_p)
    y2 = y * cos_p - z1 * sin_p
    z2 = y * sin_p + z1 * cos_p
    return cx + x1 * scale, cy - y2 * scale, z2

angles = [(45, 20), (135, 20), (225, 20), (315, 20), (0, 90)]
w, h = 300, 300
img = Image.new('RGB', (w * len(angles), h), (20, 24, 30))
draw = ImageDraw.Draw(img)

# Load palette
import json
data_json = json.load(open('analysis/viewer/assets_database.json'))
palette = data_json['metadata']['palette']

for a_idx, (yaw, pitch) in enumerate(angles):
    ox = a_idx * w
    proj_faces = []
    for f in all_faces:
        pts = [project(all_verts[idx], yaw, pitch, cx=ox + w//2, cy=h//2) for idx in f['indices']]
        avg_z = sum(p[2] for p in pts) / len(pts)
        col_idx = f['col'] % len(palette)
        rgb = tuple(palette[col_idx])
        proj_faces.append((avg_z, [(p[0], p[1]) for p in pts], rgb, f['indices']))
    proj_faces.sort(key=lambda x: x[0])
    for avg_z, pts, rgb, indices in proj_faces:
        draw.polygon(pts, fill=rgb, outline=(255, 255, 255))
    draw.text((ox + 10, 10), f"Yaw {yaw}, Pitch {pitch}", fill=(255, 255, 255))

img.save('analysis/test_m113_solved.png')
print("Saved analysis/test_m113_solved.png")
