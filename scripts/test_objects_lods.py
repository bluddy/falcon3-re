import struct
import math
from PIL import Image, ImageDraw

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

lods = [
    (0, struct.unpack_from('<3H', obj, 0x40)),
    (1, struct.unpack_from('<3H', obj, 0x4a)),
    (2, struct.unpack_from('<3H', obj, 0x54)),
    (3, struct.unpack_from('<3H', obj, 0x5e))
]

def render_lod(lod_idx, vc, vo, to, next_to):
    raw_verts = [struct.unpack_from('<hhh', obj, vo + i*6) for i in range(vc)]
    verts = [[v[1] / 10.0, v[2] / 10.0, -v[0] / 10.0] for v in raw_verts]
    
    faces = []
    unique = set()
    for p in range(to, min(len(obj) - 8, next_to), 2):
        norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
        if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= len(obj):
            v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
            if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
                if v_words[0] == v_words[-1]:
                    ring = [w // 16 for w in v_words[:-1]]
                    k = tuple(sorted(ring))
                    if k not in unique:
                        unique.add(k)
                        faces.append({'color': col & 0xFF, 'indices': ring})
    return verts, faces

lod_limits = [0x874, 0xb28, 0xbe0, len(obj)]
results = []
for idx, (lod_num, (vc, vo, to)) in enumerate(lods):
    verts, faces = render_lod(lod_num, vc, vo, to, lod_limits[idx])
    results.append((lod_num, vc, len(faces), verts, faces))
    print(f"LOD {lod_num}: {vc} verts, {len(faces)} faces")

W, H = 1000, 750
img = Image.new('RGB', (W, H), (10, 14, 23))
draw = ImageDraw.Draw(img)

def proj_gl(x, y, z):
    rad30 = math.radians(30)
    rad20 = math.radians(20)
    sx = x * math.cos(rad30) + z * math.sin(rad30)
    sy = -y * math.cos(rad20) + (-x * math.sin(rad30) + z * math.cos(rad30)) * math.sin(rad20)
    return sx, sy

quads = [(0, 0), (500, 0), (0, 375), (500, 375)]

for (lod_num, vc, fc, verts, faces), (qx, qy) in zip(results, quads):
    draw.rectangle([qx+8, qy+8, qx+492, qy+367], outline=(30, 41, 59))
    draw.text((qx+16, qy+16), f"OBJECTS F16 - LOD {lod_num} ({vc}v, {fc}f)", fill=(56, 189, 248))
    
    if not verts or not faces: continue
    valid_verts = verts[4:] if len(verts) > 10 else verts
    pts2d = [proj_gl(v[0], v[1], v[2]) for v in verts]
    valid_pts = [proj_gl(v[0], v[1], v[2]) for v in valid_verts]
    
    min_x = min(p[0] for p in valid_pts)
    max_x = max(p[0] for p in valid_pts)
    min_y = min(p[1] for p in valid_pts)
    max_y = max(p[1] for p in valid_pts)
    span = max(max_x - min_x, max_y - min_y, 0.1)
    
    scale = 260 / span
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    ox = qx + 250
    oy = qy + 195
    
    screen_pts = [(ox + (p[0] - cx) * scale, oy + (p[1] - cy) * scale) for p in pts2d]
    
    for f in faces:
        poly = [screen_pts[i] for i in f['indices']]
        col = f['color']
        rgb = (col, min(255, col + 20), min(255, col + 40))
        draw.polygon(poly, fill=rgb, outline=(6, 182, 212))

out_path = 'analysis/test_objects_f16_lods.png'
img.save(out_path)
print(f"Saved to {out_path}")
