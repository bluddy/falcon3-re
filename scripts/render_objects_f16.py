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

# Authentic Falcon 3.0 OBJECTS coordinate system:
# X = Length (fuselage, nose +X, tail -X)
# Y = Lateral (wingspan, right +Y, left -Y)
# Z = Vertical (height, up +Z, down -Z)
# For standard 3D viewer (where Y is up, Z is depth/forward):
# Viewer X = Y
# Viewer Y = Z
# Viewer Z = X
verts = [[v[0] / 10.0, v[1] / 10.0, v[2] / 10.0] for v in raw_verts]

def parse_object_node(data, p, vc):
    if p + 8 > len(data):
        return []
    norm, mode, col, cnt = struct.unpack_from('<4H', data, p)
    faces = []
    if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= len(data):
        v_words = struct.unpack_from(f'<{cnt+1}H', data, p + 8)
        if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
            ring = [w // 16 for w in v_words[:-1]]
            faces.append({'color': col & 0xFF, 'indices': ring, 'offset': p})
            next_p = p + 8 + (cnt + 1) * 2
            while next_p + 8 <= len(data):
                n2, m2, c2, cnt2 = struct.unpack_from('<4H', data, next_p)
                if 3 <= cnt2 <= 16 and next_p + 8 + (cnt2 + 1) * 2 <= len(data):
                    v_words2 = struct.unpack_from(f'<{cnt2+1}H', data, next_p + 8)
                    if all(w % 16 == 0 and (w // 16) < vc for w in v_words2):
                        ring2 = [w // 16 for w in v_words2[:-1]]
                        faces.append({'color': c2 & 0xFF, 'indices': ring2, 'offset': next_p})
                        next_p += 8 + (cnt2 + 1) * 2
                        continue
                break
    return faces

octant_ptrs = [0x0232, 0x0288, 0x02de, 0x0330, 0x0382, 0x03ce, 0x041a, 0x0466]
all_node_ptrs = set()

for oct_ptr in octant_ptrs:
    p = oct_ptr
    if struct.unpack_from('<H', obj, p)[0] == 0xFFFF:
        p += 2
    while p + 2 <= len(obj):
        node = struct.unpack_from('<H', obj, p)[0]
        p += 2
        if node == 0xFFFF or node == 0:
            break
        if 0x400 <= node < len(obj):
            all_node_ptrs.add(node)

all_faces = []
unique_rings = set()
for node in sorted(all_node_ptrs):
    for f in parse_object_node(obj, node, vc):
        k = tuple(sorted(f['indices']))
        if k not in unique_rings:
            unique_rings.add(k)
            all_faces.append(f)

print(f"Total verts: {len(verts)}, faces: {len(all_faces)}")

W, H = 1000, 750
img = Image.new('RGB', (W, H), (10, 14, 23))
draw = ImageDraw.Draw(img)

# Now correct projection views:
# Top view: X (length) along horizontal, Y (wingspan) along vertical -> (x, -y)
# Side view: X (length) along horizontal, Z (height) along vertical -> (x, -z)
# Front view: Y (wingspan) along horizontal, Z (height) along vertical -> (y, -z)
# Iso: 3D perspective
views = [
    ('Top View (XY)', 0, 0, 500, 375, lambda x,y,z: (x, -y)),
    ('Side View (XZ)', 500, 0, 500, 375, lambda x,y,z: (x, -z)),
    ('Front View (YZ)', 0, 375, 500, 375, lambda x,y,z: (y, -z)),
    ('Isometric View', 500, 375, 500, 375, lambda x,y,z: (
        (x * math.cos(math.radians(35)) - y * math.sin(math.radians(35))),
        -(z * math.cos(math.radians(25)) + (x * math.sin(math.radians(35)) + y * math.cos(math.radians(35))) * math.sin(math.radians(25)))
    ))
]

draw.text((20, 10), f'game/OBJECTS: F16 (LOD 0) - {len(verts)} Vertices, {len(all_faces)} Faces', fill=(16, 185, 129))

for title, vx, vy, vw, vh, proj in views:
    draw.rectangle([vx+8, vy+25, vx+vw-8, vy+vh-8], outline=(30, 41, 59))
    draw.text((vx+16, vy+35), title, fill=(56, 189, 248))
    
    # Exclude sentinel verts
    valid_verts = verts[4:]
    pts2d = [proj(v[0], v[1], v[2]) for v in verts]
    valid_pts = [proj(v[0], v[1], v[2]) for v in valid_verts]
    
    min_x = min(p[0] for p in valid_pts)
    max_x = max(p[0] for p in valid_pts)
    min_y = min(p[1] for p in valid_pts)
    max_y = max(p[1] for p in valid_pts)
    span = max(max_x - min_x, max_y - min_y, 0.1)
    
    scale = (min(vw, vh) - 90) / span
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    ox = vx + vw / 2
    oy = vy + vh / 2
    
    screen_pts = [(ox + (p[0] - cx) * scale, oy + (p[1] - cy) * scale) for p in pts2d]
    
    for f in all_faces:
        poly = [screen_pts[idx] for idx in f['indices']]
        col = f['color']
        rgb = (col, min(255, col + 20), min(255, col + 40))
        draw.polygon(poly, fill=rgb, outline=(6, 182, 212))

out_path = 'analysis/test_objects_f16_turnaround.png'
img.save(out_path)
print(f"Saved turnaround render to {out_path}")
