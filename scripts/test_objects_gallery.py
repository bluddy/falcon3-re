import struct
import math
from PIL import Image, ImageDraw

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

def extract_object(idx):
    off = offsets[idx]
    next_off = offsets[idx+1] if idx+1 < num_objs else len(data)
    obj = data[off:next_off]
    name = obj[4:12].decode('ascii', errors='ignore').replace('\x00', '').strip()
    
    # Check LOD 0 header at 0x40
    vc, vo, to = struct.unpack_from('<3H', obj, 0x40)
    if vc == 0 or vo >= len(obj) or vo + vc*6 > len(obj):
        return None
    
    raw_verts = [struct.unpack_from('<hhh', obj, vo + i*6) for i in range(vc)]
    # Falcon 3.0 OBJECTS coords: X=length, Y=wingspan, Z=height
    # Viewer coords: X=length, Y=height (up), Z=wingspan
    # For 3D view: x = v[0]/10, y = v[2]/10, z = v[1]/10
    verts = [[v[0] / 10.0, v[1] / 10.0, v[2] / 10.0] for v in raw_verts]
    
    # Scan for nodes in range
    # LOD 1 offset:
    next_lod_to = struct.unpack_from('<H', obj, 0x4e)[0]
    if next_lod_to == 0 or next_lod_to > len(obj):
        next_lod_to = len(obj)
    
    faces = []
    unique = set()
    # Scan between to and next_lod_to or len(obj)
    for p in range(to, min(len(obj) - 8, next_lod_to), 2):
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
    
    return {
        'idx': idx,
        'name': name,
        'vc': vc,
        'fc': len(faces),
        'verts': verts,
        'faces': faces
    }

test_indices = [2, 4, 6, 7] # F15, FA18, F4, A4
results = []
for idx in test_indices:
    m = extract_object(idx)
    if m:
        results.append(m)
        print(f"Extracted {m['name']} (Obj {idx}): {m['vc']} verts, {m['fc']} faces")

W, H = 1000, 750
img = Image.new('RGB', (W, H), (10, 14, 23))
draw = ImageDraw.Draw(img)

# Render 4 aircraft in 4 quadrants (Isometric view)
quads = [(0, 0), (500, 0), (0, 375), (500, 375)]
proj = lambda x,y,z: (
    (x * math.cos(math.radians(35)) - y * math.sin(math.radians(35))),
    -(z * math.cos(math.radians(25)) + (x * math.sin(math.radians(35)) + y * math.cos(math.radians(35))) * math.sin(math.radians(25)))
)

for m, (qx, qy) in zip(results, quads):
    draw.rectangle([qx+8, qy+8, qx+492, qy+367], outline=(30, 41, 59))
    draw.text((qx+16, qy+16), f"Obj {m['idx']:02d}: {m['name']} ({m['vc']}v, {m['fc']}f)", fill=(56, 189, 248))
    
    verts = m['verts']
    valid_verts = verts[4:] if len(verts) > 10 else verts
    pts2d = [proj(v[0], v[1], v[2]) for v in verts]
    valid_pts = [proj(v[0], v[1], v[2]) for v in valid_verts]
    
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
    
    for f in m['faces']:
        poly = [screen_pts[i] for i in f['indices']]
        col = f['color']
        rgb = (col, min(255, col + 20), min(255, col + 40))
        draw.polygon(poly, fill=rgb, outline=(6, 182, 212))

out_path = 'analysis/test_objects_gallery.png'
img.save(out_path)
print(f"Saved gallery to {out_path}")
