import struct
import math
from PIL import Image, ImageDraw

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
obj = data[offsets[3]:offsets[4]] # F-16

sig = obj.find(b'\xff\xff\x00\x40')
table_p = sig + 4

vc0, vo0, to0, _, _ = struct.unpack_from('<5H', obj, table_p)
vc1, vo1, to1, _, _ = struct.unpack_from('<5H', obj, table_p + 10)
raw_verts = [struct.unpack_from('<hhh', obj, vo0 + i*6) for i in range(vc0)]

# Authentic NED -> OpenGL transform:
# NED: X=forward, Y=right, Z=down
# OpenGL: X=right, Y=up, Z=depth (nose toward +Z like REPORT.DAT, or -Z)
# In REPORT.DAT: nose is along +Z, right wing along +X, up along +Y.
verts_new = [[v[1] / 10.0, -v[2] / 10.0, v[0] / 10.0] for v in raw_verts]

# Bounded faces strictly within LOD 0 [to0 .. to1]
faces_clean = []
unique = set()
for p in range(to0, to1 - 8, 2):
    norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
    if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= to1:
        v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
        if all(w % 16 == 0 and (w // 16) < vc0 for w in v_words):
            if v_words[0] == v_words[-1]:
                ring = [w // 16 for w in v_words[:-1]]
                k = tuple(sorted(ring))
                if k not in unique:
                    unique.add(k)
                    faces_clean.append({'col': col & 0xFF, 'ring': ring})

print(f"Authentic F-16: {len(verts_new)} verts, {len(faces_clean)} faces")

W, H = 1000, 750
img = Image.new('RGB', (W, H), (15, 20, 26))
draw = ImageDraw.Draw(img)

def render_view(ox, oy, scale, transform_fn, title):
    draw.rectangle([ox - 230, oy - 160, ox + 230, oy + 160], outline=(40, 50, 60), fill=(20, 26, 34))
    draw.text((ox - 220, oy - 150), title, fill=(240, 220, 120))
    
    poly_depths = []
    for f in faces_clean:
        pts = [verts_new[vi] for vi in f['ring']]
        avg_z = sum(p[2] for p in pts) / len(pts)
        t_pts = []
        for p in pts:
            sx, sy = transform_fn(p[0], p[1], p[2])
            t_pts.append((ox + sx * scale, oy + sy * scale))
        poly_depths.append((avg_z, t_pts, f['col']))
    
    poly_depths.sort(key=lambda x: x[0], reverse=True)
    
    # Aircraft grey VGA palette
    for _, t_pts, col in poly_depths:
        # Shading by color index (140..160)
        c_val = min(220, max(80, (col - 130) * 10 + 100))
        fill_c = (c_val, c_val + 5, c_val + 15)
        outline_c = (max(0, c_val - 40), max(0, c_val - 35), max(0, c_val - 25))
        draw.polygon(t_pts, fill=fill_c, outline=outline_c)

# 4 views
def t_persp(x, y, z):
    rad35, rad20 = math.radians(35), math.radians(20)
    sx = x * math.cos(rad35) - z * math.sin(rad35)
    sy = -y * math.cos(rad20) + (x * math.sin(rad35) + z * math.cos(rad35)) * math.sin(rad20)
    return sx, sy

def t_top(x, y, z):
    return x, -z

def t_side(x, y, z):
    return -z, -y

def t_front(x, y, z):
    return x, -y

scale = 8.5
render_view(250, 190, scale, t_persp, "3D Isometric View (NED Corrected)")
render_view(750, 190, scale, t_top, "Top-Down View (Wings Spread)")
render_view(250, 550, scale, t_side, "Side Profile (Fin Up, Belly Down)")
render_view(750, 550, scale, t_front, "Front Profile (Intake Below, Canopy Above)")

draw.text((320, 20), f"AUTHENTIC F-16 IN-FLIGHT MESH (No Phantom Faces: {len(verts_new)}v, {len(faces_clean)}f)", fill=(255, 215, 0))
img.save("analysis/test_f16_authentic_ned.png")
print("Saved analysis/test_f16_authentic_ned.png")
