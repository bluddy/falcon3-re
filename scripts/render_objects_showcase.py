import json
import math
from PIL import Image, ImageDraw

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

objs = {o['id']: o for o in db['vehicles_and_units']}
pal = db.get('palette', [])

showcase_ids = [
    (0, "F-14 Tomcat (Clean Airframe)"),
    (1, "Panavia Tornado"),
    (3, "F-16 Fighting Falcon"),
    (17, "MiG-29 Fulcrum"),
    (11, "AH-64 Apache Helicopter"),
    (34, "M60 Main Battle Tank"),
    (38, "Walid APC"),
    (67, "USS Nimitz (CVN-68)")
]

W, H = 1400, 750
img = Image.new('RGB', (W, H), (12, 16, 22))
draw = ImageDraw.Draw(img)

draw.text((450, 15), "FALCON 3.0 AUTHENTIC 'OBJECTS' 3D ASSET SHOWCASE", fill=(255, 215, 0))
draw.text((470, 35), "Authentic In-Flight & Battlefield Models (NED Orientation, No Phantom Polys)", fill=(160, 180, 200))

def render_cell(ox, oy, model, title):
    draw.rectangle([ox - 150, oy - 110, ox + 150, oy + 110], outline=(35, 45, 60), fill=(18, 22, 30))
    vc = model['vertex_count']
    fc = model['face_count']
    lods = len(model.get('lods', []))
    draw.text((ox - 140, oy - 100), title, fill=(240, 220, 120))
    draw.text((ox - 140, oy + 90), f"{vc} verts | {fc} faces | {lods} LODs", fill=(140, 160, 180))
    
    verts = model['vertices']
    faces = model['faces']
    if not verts or not faces:
        return
    
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    span = max(max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs), 1.0)
    scale = 130.0 / span
    cx = (max(xs) + min(xs)) / 2.0
    cy = (max(ys) + min(ys)) / 2.0
    cz = (max(zs) + min(zs)) / 2.0
    
    # 3D isometric view: yaw 35 deg, pitch 22 deg
    rad35 = math.radians(35)
    rad22 = math.radians(22)
    cos35, sin35 = math.cos(rad35), math.sin(rad35)
    cos22, sin22 = math.cos(rad22), math.sin(rad22)
    
    poly_depths = []
    for f_item in faces:
        ring = f_item['indices']
        pts = [verts[vi] for vi in ring]
        avg_z = sum(p[2] for p in pts) / len(pts)
        t_pts = []
        for p in pts:
            px, py, pz = p[0] - cx, p[1] - cy, p[2] - cz
            sx = px * cos35 - pz * sin35
            sy = -py * cos22 + (px * sin35 + pz * cos35) * sin22
            t_pts.append((ox + sx * scale, oy + sy * scale))
        
        col_idx = f_item.get('color', 142)
        if col_idx < len(pal):
            rgb = tuple(pal[col_idx])
        else:
            rgb = (120, 140, 130)
        if rgb[0] < 20 and rgb[1] < 20 and rgb[2] < 20:
            rgb = (40, 48, 55)
        poly_depths.append((avg_z, t_pts, rgb))
    
    poly_depths.sort(key=lambda x: x[0], reverse=True)
    for _, t_pts, rgb in poly_depths:
        outline_rgb = (max(0, rgb[0]-35), max(0, rgb[1]-35), max(0, rgb[2]-35))
        draw.polygon(t_pts, fill=rgb, outline=outline_rgb)

grid = [
    (190, 190), (550, 190), (910, 190), (1270, 190),
    (190, 520), (550, 520), (910, 520), (1270, 520)
]

for (target_id, title), (gx, gy) in zip(showcase_ids, grid):
    model = objs[target_id]
    render_cell(gx, gy, model, title)

img.save("analysis/test_objects_showcase_gallery.png")
print("Saved analysis/test_objects_showcase_gallery.png")
