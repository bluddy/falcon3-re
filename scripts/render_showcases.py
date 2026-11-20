import json
import math
from PIL import Image, ImageDraw

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

rep = db['tactical_reference']
selected_names = ['F-16 FIGHTING FALCON', 'MIG-29 FULCRUM', 'SU-27 FLANKER', 'F-15 EAGLE', 'UDALOY-CLASS DESTROYER']
models_to_render = []
for name in selected_names:
    for m in rep:
        if name in m['name'].upper():
            models_to_render.append(m)
            break

for m in models_to_render:
    verts = m['vertices']
    faces = m['faces']
    name = m['name']
    
    W, H = 800, 600
    img = Image.new('RGB', (W, H), (18, 22, 28))
    draw = ImageDraw.Draw(img)
    
    views = [
        ('Top View (XZ)', 0, 0, 400, 300, lambda x,y,z: (x, -z)),
        ('Side View (ZY)', 400, 0, 400, 300, lambda x,y,z: (z, -y)),
        ('Front View (XY)', 0, 300, 400, 300, lambda x,y,z: (x, -y)),
        ('Isometric View', 400, 300, 400, 300, lambda x,y,z: (
            (x * math.cos(math.radians(30)) - z * math.sin(math.radians(30))),
            -(y * math.cos(math.radians(20)) + (x * math.sin(math.radians(30)) + z * math.cos(math.radians(30))) * math.sin(math.radians(20)))
        ))
    ]
    
    draw.text((15, 10), f'{name} - {len(verts)} Verts, {len(faces)} Faces (REPORT.DAT)', fill=(220, 240, 255))
    
    for title, vx, vy, vw, vh, proj in views:
        draw.rectangle([vx+5, vy+25, vx+vw-5, vy+vh-5], outline=(40, 50, 65))
        draw.text((vx+15, vy+35), title, fill=(160, 190, 220))
        
        valid_indices = range(4, len(verts)) if len(verts) > 10 else range(len(verts))
        pts2d = [proj(v[0], v[1], v[2]) for v in verts]
        valid_pts = [pts2d[i] for i in valid_indices]
        if not valid_pts: continue
        min_x = min(p[0] for p in valid_pts)
        max_x = max(p[0] for p in valid_pts)
        min_y = min(p[1] for p in valid_pts)
        max_y = max(p[1] for p in valid_pts)
        span = max(max_x - min_x, max_y - min_y, 0.1)
        scale = (min(vw, vh - 30) * 0.75) / span
        cx = vx + vw / 2
        cy = vy + 25 + (vh - 25) / 2
        mid_x = (min_x + max_x) / 2
        mid_y = (min_y + max_y) / 2
        screen_pts = [(cx + (p[0] - mid_x) * scale, cy + (p[1] - mid_y) * scale) for p in pts2d]
        
        for f in faces:
            ring = f['indices']
            poly_pts = [screen_pts[i] for i in ring if i < len(screen_pts)]
            for p1, p2 in zip(poly_pts, poly_pts[1:] + [poly_pts[0]]):
                draw.line([p1, p2], fill=(100, 200, 255), width=1)
                
    safe_name = name.lower().replace(' ', '_').replace('/', '_').replace('-', '_')
    out_file = f'analysis/showcase_{safe_name}.png'
    img.save(out_file)
    print(f'Rendered {out_file}')
