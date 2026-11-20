import json
import math
from PIL import Image, ImageDraw, ImageFont

data = json.load(open('analysis/viewer/assets_database.json'))
rep_m113 = [x for x in data['tactical_reference'] if '113' in x['name'].upper()][0]
obj_m113 = [x for x in data['vehicles_and_units'] if '113' in x['name'].upper()][0]

palette = data['metadata']['palette']

def project(v, yaw, pitch, scale=12.0, cx=200, cy=200):
    # v is (x, y, z)
    x, y, z = v
    # yaw around Y
    rad_y = math.radians(yaw)
    cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)
    x1 = x * cos_y + z * sin_y
    z1 = -x * sin_y + z * cos_y
    # pitch around X
    rad_p = math.radians(pitch)
    cos_p, sin_p = math.cos(rad_p), math.sin(rad_p)
    y2 = y * cos_p - z1 * sin_p
    z2 = y * sin_p + z1 * cos_p
    # 2D projection (Y up, screen Y down)
    sx = cx + x1 * scale
    sy = cy - y2 * scale
    return sx, sy, z2

def render_model(model, yaw, pitch, img_size=(400, 400), scale=10.0):
    img = Image.new('RGB', img_size, (25, 28, 35))
    draw = ImageDraw.Draw(img)
    verts = model['vertices']
    faces = model['faces']
    
    # Project faces with painter's algorithm
    proj_faces = []
    for f in faces:
        pts = []
        avg_z = 0
        valid = True
        for idx in f['indices']:
            if idx >= len(verts):
                valid = False
                break
            sx, sy, sz = project(verts[idx], yaw, pitch, scale=scale, cx=img_size[0]//2, cy=img_size[1]//2)
            pts.append((sx, sy))
            avg_z += sz
        if valid and len(pts) >= 3:
            avg_z /= len(pts)
            # compute 2D normal for backface culling
            # (p1.x - p0.x)*(p2.y - p0.y) - (p1.y - p0.y)*(p2.x - p0.x)
            c = (pts[1][0] - pts[0][0]) * (pts[2][1] - pts[0][1]) - (pts[1][1] - pts[0][1]) * (pts[2][0] - pts[0][0])
            col_idx = f['color'] % len(palette)
            rgb = tuple(palette[col_idx])
            proj_faces.append((avg_z, c, pts, rgb, f['indices']))
            
    proj_faces.sort(key=lambda item: item[0])
    
    for avg_z, c, pts, rgb, indices in proj_faces:
        draw.polygon(pts, fill=rgb, outline=(255, 255, 255, 128))
        # Draw indices
        for p_idx, pt in zip(indices, pts):
            draw.text((pt[0]+2, pt[1]+2), str(p_idx), fill=(255, 255, 0))
            
    return img

angles = [(45, 20), (135, 20), (225, 20), (315, 20), (0, 90)]
w, h = 300, 300
canvas = Image.new('RGB', (w * 5, h * 2), (15, 18, 22))
draw_c = ImageDraw.Draw(canvas)

# Row 1: REPORT.DAT M113
for i, (yaw, pitch) in enumerate(angles):
    im = render_model(rep_m113, yaw, pitch, img_size=(w, h), scale=7.0)
    canvas.paste(im, (i * w, 0))
    draw_c.text((i * w + 10, 10), f"REPORT: yaw={yaw}, pitch={pitch}", fill=(200, 255, 200))

# Row 2: OBJECTS M113
for i, (yaw, pitch) in enumerate(angles):
    im = render_model(obj_m113, yaw, pitch, img_size=(w, h), scale=18.0) # scaled to match visual size
    canvas.paste(im, (i * w, h))
    draw_c.text((i * w + 10, h + 10), f"OBJECTS: yaw={yaw}, pitch={pitch}", fill=(200, 200, 255))

canvas.save('analysis/compare_m113_turnaround.png')
print("Saved analysis/compare_m113_turnaround.png")
