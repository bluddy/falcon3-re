import sys
import math
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import QPointF
import json

# Load palette
pal = []
with open('game/ALTPAL.ISR', 'rb') as f:
    d = f.read()
for i in range(len(d)//3):
    pal.append([d[i*3]*4, d[i*3+1]*4, d[i*3+2]*4])

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

for obj in db['vehicles_and_units']:
    if 'F16' in obj['name']:
        f16 = obj
        break

verts = [list(v) for v in f16['vertices']]
# Fix nozzle Z
verts[48][2] = 11.5
verts[69][2] = 11.5
verts[72][2] = 11.5

faces = []
for f in f16['faces']:
    ring = list(f['indices'])
    col = f['color']
    # Check for bowtie quad like [23, 24, 22, 21]
    if len(ring) == 4:
        # Check if line (0-1) and (2-3) or (1-2) and (0-3) cross
        p0, p1, p2, p3 = verts[ring[0]], verts[ring[1]], verts[ring[2]], verts[ring[3]]
        # If strip order [0, 1, 2, 3], triangulate as [0, 1, 2] and [1, 3, 2]
        if ring == [23, 24, 22, 21]:
            faces.append({'color': col, 'indices': [23, 24, 21, 22]})
            continue
        elif ring == [46, 40, 64, 70]:
            # This is underbelly chine
            faces.append({'color': col, 'indices': [46, 40, 64, 70]})
            continue
    faces.append({'color': col, 'indices': ring})

# Render 4 views with QPainter (Rear, Top, Side, Iso)
app = QApplication.instance() or QApplication(sys.argv)
w, h = 1200, 900
img = QImage(w, h, QImage.Format.Format_RGB32)
img.fill(QColor(10, 14, 23)) # dark slate

painter = QPainter(img)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)

views = [
    ('Rear View (Afterburner Hexagon)', 0.0, 180.0, 0, 0),
    ('Top View (Wings & Planform)', 90.0, 0.0, 600, 0),
    ('Side View (Fuselage Profile)', 0.0, 90.0, 0, 450),
    ('Perspective Isometric View', 30.0, -45.0, 600, 450)
]

for title, rot_x, rot_y, vx, vy in views:
    painter.save()
    painter.translate(vx + 300, vy + 225)
    
    # Title
    painter.setPen(QColor(56, 189, 248))
    painter.drawText(-280, -195, title)

    # Sort faces by depth
    rad_x = math.radians(rot_x)
    rad_y = math.radians(rot_y)

    # Project vertices
    proj_verts = []
    for v in verts:
        # Rotate Y
        x1 = v[0] * math.cos(rad_y) - v[2] * math.sin(rad_y)
        z1 = v[0] * math.sin(rad_y) + v[2] * math.cos(rad_y)
        # Rotate X
        y2 = v[1] * math.cos(rad_x) - z1 * math.sin(rad_x)
        z2 = v[1] * math.sin(rad_x) + z1 * math.cos(rad_x)
        scale = 14.0
        sx = x1 * scale
        sy = -y2 * scale
        proj_verts.append((sx, sy, z2))

    # Backface culling & depth sorting
    sorted_faces = []
    for f in faces:
        ring = f['indices']
        if len(ring) < 3: continue
        p0 = proj_verts[ring[0]]
        p1 = proj_verts[ring[1]]
        p2 = proj_verts[ring[2]]
        # 2D cross product for culling
        cross = (p1[0]-p0[0])*(p2[1]-p0[1]) - (p1[1]-p0[1])*(p2[0]-p0[0])
        avg_z = sum(proj_verts[vi][2] for vi in ring) / len(ring)
        sorted_faces.append((avg_z, cross, f))

    sorted_faces.sort(key=lambda x: x[0]) # back to front

    for avg_z, cross, f in sorted_faces:
        # Only draw if not back-facing (or draw all if cross product small)
        ring = f['indices']
        poly = QPolygonF([QPointF(proj_verts[vi][0], proj_verts[vi][1]) for vi in ring])
        col = f['color']
        rgb = pal[col] if col < len(pal) else [160, 160, 160]
        # Highlight afterburner (Face 12)
        if f == faces[12]:
            painter.setBrush(QBrush(QColor(255, 140, 20, 230)))
            painter.setPen(QPen(QColor(255, 220, 0), 2.5))
        else:
            painter.setBrush(QBrush(QColor(rgb[0], rgb[1], rgb[2])))
            painter.setPen(QPen(QColor(0, 200, 255, 120), 1.0))
        painter.drawPolygon(poly)

    painter.restore()

painter.end()
img.save('analysis/viewer/f16_verified_afterburner_wings.png')
print("Successfully generated analysis/viewer/f16_verified_afterburner_wings.png")
