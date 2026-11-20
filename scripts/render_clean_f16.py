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

vc, vo, to = struct.unpack_from('<3H', obj, 0x40)
raw_verts = [struct.unpack_from('<hhh', obj, vo + i*6) for i in range(vc)]

# Test modifying v46 from (250, -20, 0) to (250, 0, 0)
# And v21 vs right wing
verts_mod = [[v[1] / 10.0, v[2] / 10.0, -v[0] / 10.0] for v in raw_verts]
verts_mod[46] = [0.0, 0.0, -25.0]

faces = []
unique = set()
for p in range(to, 0x874, 2):
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

W, H = 1000, 750
img = Image.new('RGB', (W, H), (10, 14, 23))
draw = ImageDraw.Draw(img)

def proj_gl(x, y, z):
    rad30 = math.radians(30)
    rad20 = math.radians(20)
    sx = x * math.cos(rad30) + z * math.sin(rad30)
    sy = -y * math.cos(rad20) + (-x * math.sin(rad30) + z * math.cos(rad30)) * math.sin(rad20)
    return sx, sy

# 4 views:
# Top View (X=lateral, Z=depth): (x, -z)
# Side View (Z=depth, Y=height): (z, -y)
# Front View (X=lateral, Y=height): (x, -y)
# Iso View
views = [
    ('Top View (XZ)', 0, 0, 500, 375, lambda x,y,z: (x, -z)),
    ('Side View (ZY)', 500, 0, 500, 375, lambda x,y,z: (z, -y)),
    ('Front View (XY)', 0, 375, 500, 375, lambda x,y,z: (x, -y)),
    ('Isometric View', 500, 375, 500, 375, proj_gl)
]

for title, qx, qy, qw, qh, proj in views:
    draw.rectangle([qx+8, qy+25, qx+qw-8, qy+qh-8], outline=(30, 41, 59))
    draw.text((qx+16, qy+35), title, fill=(56, 189, 248))
    
    valid_verts = verts_mod[4:]
    pts2d = [proj(v[0], v[1], v[2]) for v in verts_mod]
    valid_pts = [proj(v[0], v[1], v[2]) for v in valid_verts]
    
    min_x = min(p[0] for p in valid_pts)
    max_x = max(p[0] for p in valid_pts)
    min_y = min(p[1] for p in valid_pts)
    max_y = max(p[1] for p in valid_pts)
    span = max(max_x - min_x, max_y - min_y, 0.1)
    
    scale = 260 / span
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    ox = qx + qw / 2
    oy = qy + qh / 2
    
    screen_pts = [(ox + (p[0] - cx) * scale, oy + (p[1] - cy) * scale) for p in pts2d]
    
    for f in faces:
        poly = [screen_pts[i] for i in f['indices']]
        col = f['color']
        rgb = (col, min(255, col + 20), min(255, col + 40))
        draw.polygon(poly, fill=rgb, outline=(6, 182, 212))

out_path = 'analysis/test_objects_f16_clean_turnaround.png'
img.save(out_path)
print(f"Saved to {out_path}")
