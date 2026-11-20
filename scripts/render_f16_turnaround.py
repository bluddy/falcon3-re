import struct
import math
import sys
from pathlib import Path
from PyQt6.QtGui import QGuiApplication, QImage, QPainter, QColor, QPolygonF, QPen, QBrush
from PyQt6.QtCore import QPointF

app = QGuiApplication(sys.argv if sys.argv else ['test'])

def render_model_views(verts, faces, out_path, title="3D Model"):
    width, height = 1200, 800
    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(QColor(18, 22, 28))
    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 4 Viewports:
    # Top-Left: Front/Perspective (elev=20, azim=-45)
    # Top-Right: Top-Down (elev=90, azim=0)
    # Bottom-Left: Side View (elev=0, azim=-90)
    # Bottom-Right: Rear 3/4 Perspective (elev=15, azim=135)
    views = [
        ("Perspective (Front 3/4)", 0, 0, 600, 400, 20, -45),
        ("Top-Down View", 600, 0, 600, 400, 88, 0),
        ("Side Profile View", 0, 400, 600, 400, 0, -90),
        ("Perspective (Rear 3/4)", 600, 400, 600, 400, 15, 135)
    ]

    # Auto-calculate scale to fit viewport
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    max_dim = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0)

    for v_title, vx, vy, vw, vh, elev_deg, azim_deg in views:
        scale = (min(vw, vh) * 0.4) / (max_dim * 0.5)
        # Draw viewport border and title
        painter.setPen(QColor(45, 55, 72))
        painter.drawRect(vx + 5, vy + 5, vw - 10, vh - 10)
        painter.setPen(QColor(200, 210, 225))
        painter.drawText(vx + 20, vy + 30, v_title)

        elev = math.radians(elev_deg)
        azim = math.radians(azim_deg)

        cos_a, sin_a = math.cos(azim), math.sin(azim)
        cos_e, sin_e = math.cos(elev), math.sin(elev)

        proj_verts = []
        for x, y, z in verts:
            # 1. Rotate Azimuth (around Y)
            rx = x * cos_a + z * sin_a
            ry = y
            rz = -x * sin_a + z * cos_a

            # 2. Rotate Elevation (around X)
            px = rx
            py = ry * cos_e - rz * sin_e
            pz = ry * sin_e + rz * cos_e

            cx = vx + vw / 2
            cy = vy + vh / 2
            sx = cx + px * scale
            sy = cy - py * scale
            proj_verts.append((sx, sy, pz))

        # Sort faces by average depth pz (painter's algorithm)
        sorted_faces = []
        for f in faces:
            ring = f if isinstance(f, list) else f['indices']
            avg_z = sum(proj_verts[idx][2] for idx in ring) / len(ring)
            sorted_faces.append((avg_z, ring))
        sorted_faces.sort(key=lambda item: item[0])

        # Draw faces
        for _, ring in sorted_faces:
            poly = QPolygonF([QPointF(proj_verts[idx][0], proj_verts[idx][1]) for idx in ring])
            
            # Simple lighting from top-front
            v0 = verts[ring[0]]
            v1 = verts[ring[1]]
            v2 = verts[ring[2]]
            ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
            bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
            nx = ay * bz - az * by
            ny = az * bx - ax * bz
            nz = ax * by - ay * bx
            nl = math.sqrt(nx*nx + ny*ny + nz*nz)
            if nl > 1e-4:
                nx, ny, nz = nx/nl, ny/nl, nz/nl
                # Dot with light (0.3, 0.8, 0.5)
                dot = max(0.1, min(1.0, nx * 0.3 + ny * 0.8 + nz * 0.5))
            else:
                dot = 0.5
            
            base_col = QColor(100, 130, 160)
            r = int(base_col.red() * dot)
            g = int(base_col.green() * dot)
            b = int(base_col.blue() * dot)

            painter.setBrush(QBrush(QColor(r, g, b, 230)))
            painter.setPen(QPen(QColor(20, 30, 45), 1))
            painter.drawPolygon(poly)

    painter.end()
    img.save(str(out_path))
    print(f"Rendered -> {out_path}")

if __name__ == '__main__':
    # Render FALCOBJ High LOD
    falc = open('game/FALCOBJ.BIN', 'rb').read()
    vc = 177
    vo = 0x164
    verts = [struct.unpack_from('<hhh', falc, vo + i*6) for i in range(vc)]
    # Convert coords: in FALCOBJ, X is lateral, Y is vertical, Z is longitudinal
    converted_verts = [[v[0], v[1], v[2]] for v in verts]

    faces = []
    visited = set()
    for p in range(0x58a, 0x1abe, 2):
        cnt = struct.unpack_from('<H', falc, p)[0]
        if 3 <= cnt <= 12 and p + 2 + (cnt+1)*2 <= 0x1abe:
            words = struct.unpack_from(f'<{cnt+1}H', falc, p + 2)
            if all(w % 16 == 0 and (w // 16) < vc for w in words):
                ring = [w // 16 for w in words[:-1]]
                norm_ring = frozenset(ring)
                if norm_ring not in visited:
                    visited.add(norm_ring)
                    faces.append(ring)

    render_model_views(converted_verts, faces, 'analysis/viewer/falcobj_high_lod_verified.png', 'FALCOBJ High LOD (177 verts, 104 faces)')
