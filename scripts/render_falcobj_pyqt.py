import struct
import math
import sys
from PyQt6.QtGui import QGuiApplication, QImage, QPainter, QColor, QPolygonF, QPen, QFont
from PyQt6.QtCore import QPointF, Qt

app = QGuiApplication(sys.argv)

# Load FALCOBJ.BIN
with open('game/FALCOBJ.BIN', 'rb') as f:
    d = f.read()

file_start = 10
vo = file_start + 0x198A

raw_verts = []
for vi in range(22):
    x, y, z = struct.unpack_from('<hhh', d, vo + vi * 6)
    # x = lateral (wingspan), y = height (up), z = forward (length)
    raw_verts.append((x, y, z))

polys = [
    ([14, 18, 19, 12, 11, 13], 'Wing Delta', QColor(74, 105, 132, 230)),
    ([16, 0, 15, 10, 1, 17], 'Tail Elevators', QColor(92, 130, 166, 230)),
    ([3, 13, 11], 'Lower Intake Nose', QColor(122, 155, 184, 230)),
    ([4, 13, 11], 'Upper Canopy Nose', QColor(59, 85, 110, 230)),
    ([2, 4, 21, 3, 7, 5], 'Centerline Spine', QColor(44, 62, 80, 230)),
    ([7, 6, 20, 5], 'Ventral Keel', QColor(36, 51, 66, 230)),
    ([21, 8, 11, 10, 15, 13, 9], 'Canopy & Fuselage', QColor(137, 169, 196, 230))
]

# Image size: 1600 x 1200
img = QImage(1600, 1200, QImage.Format.Format_ARGB32)
img.fill(QColor(25, 28, 35))

painter = QPainter(img)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)

views = [
    ("Isometric 3/4 View", 0, 0, 800, 600, 25, 45),
    ("Top Planform View (Wings & Delta)", 800, 0, 800, 600, 90, 0),
    ("Side Profile View", 0, 600, 800, 600, 0, 90),
    ("Front View", 800, 600, 800, 600, 0, 0)
]

def project(vx, vy, vz, pitch_deg, yaw_deg, cx, cy, scale=1.4):
    p_rad = math.radians(pitch_deg)
    y_rad = math.radians(yaw_deg)
    
    # Yaw rotation around Y (up)
    x1 = vx * math.cos(y_rad) + vz * math.sin(y_rad)
    y1 = vy
    z1 = -vx * math.sin(y_rad) + vz * math.cos(y_rad)
    
    # Pitch rotation around X (right)
    x2 = x1
    y2 = y1 * math.cos(p_rad) - z1 * math.sin(p_rad)
    z2 = y1 * math.sin(p_rad) + z1 * math.cos(p_rad)
    
    sx = cx + x2 * scale
    sy = cy - y2 * scale # Invert Y for screen coordinates
    return sx, sy, z2

for title, vx0, vy0, vw, vh, pitch, yaw in views:
    cx = vx0 + vw // 2
    cy = vy0 + vh // 2
    
    # Draw border
    painter.setPen(QPen(QColor(60, 65, 80), 1))
    painter.drawRect(vx0 + 10, vy0 + 10, vw - 20, vh - 20)
    
    # Title
    painter.setPen(QPen(QColor(0, 255, 204), 1))
    font = QFont("Arial", 14, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(vx0 + 25, vy0 + 40, title)
    
    # Project polygons and sort by depth (Painter's algorithm)
    proj_polys = []
    for indices, name, col in polys:
        pts = []
        depths = []
        for idx in indices:
            vx, vy, vz = raw_verts[idx]
            sx, sy, sz = project(vx, vy, vz, pitch, yaw, cx, cy)
            pts.append(QPointF(sx, sy))
            depths.append(sz)
        avg_depth = sum(depths) / len(depths)
        proj_polys.append((avg_depth, pts, col, name))
        
    # Sort back-to-front
    proj_polys.sort(key=lambda item: item[0])
    
    for _, pts, col, _ in proj_polys:
        qpoly = QPolygonF(pts)
        painter.setBrush(col)
        painter.setPen(QPen(QColor(220, 240, 255, 220), 1.5))
        painter.drawPolygon(qpoly)
        
    # Draw vertices
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(0, 255, 204, 230))
    for vi, (vx, vy, vz) in enumerate(raw_verts):
        sx, sy, sz = project(vx, vy, vz, pitch, yaw, cx, cy)
        painter.drawEllipse(QPointF(sx, sy), 3.0, 3.0)

painter.end()

out_path = 'analysis/viewer/f16_falcobj_rendered.png'
img.save(out_path)
print(f"Rendered image successfully saved to {out_path}!")
