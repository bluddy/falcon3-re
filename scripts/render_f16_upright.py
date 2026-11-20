import json
import math
from PIL import Image, ImageDraw

data = json.load(open('analysis/viewer/assets_database.json'))
obj_f16 = [x for x in data['vehicles_and_units'] if x['name'].upper() == 'F16'][0]
palette = data['metadata']['palette']

def project(v, yaw, pitch, scale=7.0, cx=150, cy=150):
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

verts = obj_f16['vertices']
faces = obj_f16['faces']

for a_idx, (yaw, pitch) in enumerate(angles):
    ox = a_idx * w
    proj_faces = []
    for f in faces:
        pts = [project(verts[idx], yaw, pitch, cx=ox + w//2, cy=h//2) for idx in f['indices']]
        avg_z = sum(p[2] for p in pts) / len(pts)
        col_idx = f['color'] % len(palette)
        rgb = tuple(palette[col_idx])
        proj_faces.append((avg_z, [(p[0], p[1]) for p in pts], rgb))
    proj_faces.sort(key=lambda x: x[0])
    for avg_z, pts, rgb in proj_faces:
        draw.polygon(pts, fill=rgb, outline=(255, 255, 255))
    draw.text((ox + 10, 10), f"F-16 (Yaw {yaw}, Pitch {pitch})", fill=(255, 255, 255))

img.save('analysis/test_f16_upright_turnaround.png')
print("Saved analysis/test_f16_upright_turnaround.png")
