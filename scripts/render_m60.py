import json
import math
from PIL import Image, ImageDraw

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

objs = {o['id']: o for o in db['vehicles_and_units']}
m60 = objs[34]

all_verts = m60['vertices']
all_faces = m60['faces']

W, H = 1000, 750
img = Image.new('RGB', (W, H), (15, 20, 25))
draw = ImageDraw.Draw(img)

def render_view(ox, oy, scale, transform_fn, title):
    draw.rectangle([ox - 230, oy - 160, ox + 230, oy + 160], outline=(40, 50, 60), fill=(20, 25, 32))
    draw.text((ox - 220, oy - 150), title, fill=(180, 200, 220))
    
    poly_depths = []
    for f in all_faces:
        pts = [all_verts[vi] for vi in f['indices']]
        avg_z = sum(p[2] for p in pts) / len(pts)
        t_pts = []
        for p in pts:
            sx, sy = transform_fn(p[0], p[1], p[2])
            t_pts.append((ox + sx * scale, oy + sy * scale))
        poly_depths.append((avg_z, t_pts, f['color']))
    
    poly_depths.sort(key=lambda x: x[0], reverse=True)
    
    c_map = {112: (80, 110, 60), 117: (90, 120, 70), 118: (100, 130, 80), 119: (110, 140, 90),
             120: (120, 150, 100), 121: (130, 160, 110), 132: (70, 95, 55), 144: (60, 85, 45),
             153: (140, 170, 120), 0: (40, 50, 35)}
    
    for _, t_pts, col in poly_depths:
        fill_c = c_map.get(col, (95, 125, 75))
        draw.polygon(t_pts, fill=fill_c, outline=(20, 30, 20))

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

scale = 10.0
render_view(250, 190, scale, t_persp, "3D Isometric View (Turret On Top)")
render_view(750, 190, scale, t_top, "Top-Down View (Chassis & Turret)")
render_view(250, 550, scale, t_side, "Side Profile View")
render_view(750, 550, scale, t_front, "Front Profile View")

draw.text((360, 20), f"AUTHENTIC M60 TANK (OBJECTS Archive: {len(all_verts)}v, {len(all_faces)}f)", fill=(255, 215, 0))
img.save("analysis/test_objects_m60_turnaround.png")
print("Saved analysis/test_objects_m60_turnaround.png")
