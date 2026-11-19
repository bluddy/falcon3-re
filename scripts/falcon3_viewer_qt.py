"""
Falcon 3.0 — Native Qt6 3D Asset & Object Inspector
Visualizes all 204 flight engine assets (Aircraft, Vehicles, Ground Structures, Ribbons)
Supports OpenGL rendering and software 3D projection fallback.
"""

import sys
import os
import math
import json
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox, QPushButton,
    QLabel, QGroupBox, QSplitter, QStatusBar, QFrame
)

# Try importing OpenGL
HAS_OPENGL = False
try:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
    import OpenGL.GL as gl
    import OpenGL.GLU as glu
    HAS_OPENGL = True
except ImportError:
    pass

class Model3DWidget(QOpenGLWidget if HAS_OPENGL else QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None
        self.palette = []
        self.lod_idx = 0
        self.render_mode = 'both' # 'shaded', 'wire', 'both'
        self.show_grid = True
        self.auto_rotate = False
        
        # Camera / Orbit state
        self.rot_x = 25.0
        self.rot_y = -45.0
        self.zoom = 50.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.last_mouse_pos = QPoint()

        # Auto-rotate timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer)
        self.timer.start(16) # ~60 fps

        # Bounding box & centered vertices
        self.centered_verts = []
        self.faces = []
        self.edges = []
        self.max_dim = 1.0

    def _on_timer(self):
        if self.auto_rotate:
            self.rot_y = (self.rot_y + 0.8) % 360.0
            self.update()

    def set_palette(self, pal):
        self.palette = pal

    def set_model(self, model, lod_idx=0):
        self.model = model
        self.lod_idx = lod_idx
        self.prepare_geometry()
        self.update()

    def set_render_mode(self, mode):
        self.render_mode = mode
        self.update()

    def set_show_grid(self, val):
        self.show_grid = val
        self.update()

    def set_auto_rotate(self, val):
        self.auto_rotate = val

    def reset_view(self):
        self.rot_x = 25.0
        self.rot_y = -45.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.zoom = max(self.max_dim * 1.8, 10.0)
        self.update()

    def set_view_preset(self, preset):
        self.pan_x = 0.0
        self.pan_y = 0.0
        if preset == 'front':
            self.rot_x = 0.0
            self.rot_y = 0.0
        elif preset == 'side':
            self.rot_x = 0.0
            self.rot_y = 90.0
        elif preset == 'top':
            self.rot_x = 90.0
            self.rot_y = 0.0
        elif preset == 'iso':
            self.rot_x = 30.0
            self.rot_y = -45.0
        self.update()

    def prepare_geometry(self):
        if not self.model:
            self.centered_verts = []
            self.faces = []
            self.edges = []
            return

        verts = self.model.get('vertices', [])
        faces = self.model.get('faces', [])
        edges = self.model.get('edges', [])

        # Check LOD
        lods = self.model.get('lods', [])
        if lods and self.lod_idx < len(lods):
            lod = lods[self.lod_idx]
            verts = lod.get('vertices', verts)
            faces = lod.get('faces', faces)
            edges = lod.get('edges', edges)

        if not verts:
            self.centered_verts = []
            self.faces = []
            self.edges = []
            return

        # Calculate bounding box
        min_x = min(v[0] for v in verts)
        max_x = max(v[0] for v in verts)
        min_y = min(v[1] for v in verts)
        max_y = max(v[1] for v in verts)
        min_z = min(v[2] for v in verts)
        max_z = max(v[2] for v in verts)

        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        cz = (min_z + max_z) / 2.0

        self.max_dim = max(max_x - min_x, max_y - min_y, max_z - min_z, 1.0)
        self.zoom = self.max_dim * 1.8

        self.centered_verts = [[v[0] - cx, v[1] - cy, v[2] - cz] for v in verts]
        self.faces = faces
        self.edges = edges

    # Mouse navigation
    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.pos().x() - self.last_mouse_pos.x()
        dy = event.pos().y() - self.last_mouse_pos.y()

        if event.buttons() & Qt.MouseButton.LeftButton:
            self.rot_y = (self.rot_y + dx * 0.5) % 360.0
            self.rot_x = max(-89.0, min(89.0, self.rot_x + dy * 0.5))
            self.update()
        elif event.buttons() & (Qt.MouseButton.RightButton | Qt.MouseButton.MiddleButton):
            factor = self.zoom * 0.002
            self.pan_x += dx * factor
            self.pan_y -= dy * factor
            self.update()

        self.last_mouse_pos = event.pos()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        zoom_factor = 0.85 if delta > 0 else 1.15
        self.zoom = max(1.0, min(2000.0, self.zoom * zoom_factor))
        self.update()

    # OpenGL pipeline
    if HAS_OPENGL:
        def initializeGL(self):
            gl.glClearColor(0.04, 0.06, 0.09, 1.0) # #0A0E17 dark slate
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glEnable(gl.GL_COLOR_MATERIAL)
            gl.glEnable(gl.GL_LIGHTING)
            gl.glEnable(gl.GL_LIGHT0)
            gl.glEnable(gl.GL_NORMALIZE)
            gl.glLightModeli(gl.GL_LIGHT_MODEL_TWO_SIDE, gl.GL_TRUE)
            gl.glDisable(gl.GL_CULL_FACE)
            gl.glShadeModel(gl.GL_SMOOTH)

            # Lights (angled sun light from upper-front-right)
            gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, [1.5, 2.0, 1.5, 0.0])
            gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, [0.95, 0.95, 0.95, 1.0])
            gl.glLightfv(gl.GL_LIGHT0, gl.GL_AMBIENT, [0.4, 0.4, 0.45, 1.0])

        def resizeGL(self, w, h):
            if h == 0: h = 1
            gl.glViewport(0, 0, w, h)
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            glu.gluPerspective(45.0, w / float(h), 0.1, 5000.0)
            gl.glMatrixMode(gl.GL_MODELVIEW)

        def paintGL(self):
            gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
            gl.glLoadIdentity()

            # Camera view
            rad_x = math.radians(self.rot_x)
            rad_y = math.radians(self.rot_y)

            eye_x = self.zoom * math.cos(rad_x) * math.sin(rad_y)
            eye_y = self.zoom * math.sin(rad_x)
            eye_z = self.zoom * math.cos(rad_x) * math.cos(rad_y)

            glu.gluLookAt(
                eye_x + self.pan_x, eye_y + self.pan_y, eye_z,
                self.pan_x, self.pan_y, 0,
                0.0, 1.0, 0.0
            )

            # Draw Ground Grid
            if self.show_grid:
                gl.glDisable(gl.GL_LIGHTING)
                gl.glColor4f(0.12, 0.16, 0.24, 0.5)
                gl.glBegin(gl.GL_LINES)
                g_size = max(self.max_dim * 1.5, 30.0)
                g_step = g_size / 10.0
                k = -g_size
                while k <= g_size:
                    gl.glVertex3f(k, -self.max_dim*0.5, -g_size)
                    gl.glVertex3f(k, -self.max_dim*0.5, g_size)
                    gl.glVertex3f(-g_size, -self.max_dim*0.5, k)
                    gl.glVertex3f(g_size, -self.max_dim*0.5, k)
                    k += g_step
                gl.glEnd()

            if not self.centered_verts:
                return

            # Render Solid Shaded Faces
            if self.faces and self.render_mode in ('shaded', 'both'):
                gl.glEnable(gl.GL_LIGHTING)
                gl.glEnable(gl.GL_POLYGON_OFFSET_FILL)
                gl.glPolygonOffset(1.0, 1.0)
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
                for f in self.faces:
                    ring = f.get('indices', [])
                    if len(ring) < 3: continue
                    col_idx = f.get('color', 142)
                    rgb = [160, 160, 160]
                    if self.palette and col_idx < len(self.palette):
                        rgb = self.palette[col_idx]
                    gl.glColor3f(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)

                    # Compute face normal for authentic Gouraud/Phong shading
                    if all(vi < len(self.centered_verts) for vi in ring[:3]):
                        p0 = self.centered_verts[ring[0]]
                        p1 = self.centered_verts[ring[1]]
                        p2 = self.centered_verts[ring[2]]
                        nx = (p1[1]-p0[1])*(p2[2]-p0[2]) - (p1[2]-p0[2])*(p2[1]-p0[1])
                        ny = (p1[2]-p0[2])*(p2[0]-p0[0]) - (p1[0]-p0[0])*(p2[2]-p0[2])
                        nz = (p1[0]-p0[0])*(p2[1]-p0[1]) - (p1[1]-p0[1])*(p2[0]-p0[0])
                        nl = math.sqrt(nx*nx + ny*ny + nz*nz)
                        if nl > 1e-6:
                            gl.glNormal3f(nx/nl, ny/nl, nz/nl)

                    gl.glBegin(gl.GL_POLYGON)
                    for vi in ring:
                        if vi < len(self.centered_verts):
                            vx, vy, vz = self.centered_verts[vi]
                            gl.glVertex3f(vx, vy, vz)
                    gl.glEnd()
                gl.glDisable(gl.GL_POLYGON_OFFSET_FILL)

            # Render Wireframe Lines
            if self.render_mode in ('wire', 'both') or not self.faces:
                gl.glDisable(gl.GL_LIGHTING)
                gl.glLineWidth(1.5)
                if self.render_mode == 'wire':
                    gl.glColor3f(0.0, 1.0, 0.4) # Retro Vector Green
                else:
                    gl.glColor3f(0.1, 0.8, 1.0) # Cyan accent outline

                gl.glBegin(gl.GL_LINES)
                if self.edges:
                    for v1, v2 in self.edges:
                        if v1 < len(self.centered_verts) and v2 < len(self.centered_verts):
                            p1 = self.centered_verts[v1]
                            p2 = self.centered_verts[v2]
                            gl.glVertex3f(p1[0], p1[1], p1[2])
                            gl.glVertex3f(p2[0], p2[1], p2[2])
                elif self.faces:
                    for f in self.faces:
                        ring = f.get('indices', [])
                        for i in range(len(ring)):
                            v1 = ring[i]
                            v2 = ring[(i + 1) % len(ring)]
                            if v1 < len(self.centered_verts) and v2 < len(self.centered_verts):
                                p1 = self.centered_verts[v1]
                                p2 = self.centered_verts[v2]
                                gl.glVertex3f(p1[0], p1[1], p1[2])
                                gl.glVertex3f(p2[0], p2[1], p2[2])
                gl.glEnd()

    else:
        # Software 3D projection fallback with QPainter
        def paintEvent(self, event):
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.fillRect(self.rect(), QtGui.QColor(10, 14, 23))

            w = self.width()
            h = self.height()
            cx, cy = w / 2.0, h / 2.0

            if not self.centered_verts:
                painter.setPen(QtGui.QColor(100, 116, 139))
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Model Selected")
                return

            rad_x = math.radians(self.rot_x)
            rad_y = math.radians(self.rot_y)
            cos_x, sin_x = math.cos(rad_x), math.sin(rad_x)
            cos_y, sin_y = math.cos(rad_y), math.sin(rad_y)

            # Project 3D -> 2D
            proj_pts = []
            focal = (w + h) / 2.0 * (50.0 / self.zoom)

            for vx, vy, vz in self.centered_verts:
                # Rotate Y
                rx1 = vx * cos_y + vz * sin_y
                ry1 = vy
                rz1 = -vx * sin_y + vz * cos_y

                # Rotate X
                rx2 = rx1
                ry2 = ry1 * cos_x - rz1 * sin_x
                rz2 = ry1 * sin_x + rz1 * cos_x + self.zoom

                if rz2 <= 1.0: rz2 = 1.0
                px = cx + (rx2 + self.pan_x) * focal / rz2
                py = cy - (ry2 + self.pan_y) * focal / rz2
                proj_pts.append((px, py, rz2))

            # Draw Edges
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 255, 100), 1.5))
            if self.edges:
                for v1, v2 in self.edges:
                    if v1 < len(proj_pts) and v2 < len(proj_pts):
                        p1, p2 = proj_pts[v1], proj_pts[v2]
                        painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))
            elif self.faces:
                for f in self.faces:
                    ring = f.get('indices', [])
                    for i in range(len(ring)):
                        v1 = ring[i]
                        v2 = ring[(i + 1) % len(ring)]
                        if v1 < len(proj_pts) and v2 < len(proj_pts):
                            p1, p2 = proj_pts[v1], proj_pts[v2]
                            painter.drawLine(int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]))


class Falcon3DViewerWindow(QMainWindow):
    def __init__(self, db_path='analysis/viewer/assets_database.json'):
        super().__init__()
        self.setWindowTitle("Falcon 3.0 — 3D Asset & Object Inspector (Qt6)")
        self.resize(1280, 800)
        self.setStyleSheet("""
            QMainWindow { background-color: #0A0E17; }
            QWidget { color: #F1F5F9; font-family: monospace, sans-serif; font-size: 12px; }
            QListWidget { background-color: #0F172A; border: 1px solid #1E293B; border-radius: 4px; padding: 4px; }
            QListWidget::item { padding: 6px 8px; border-radius: 4px; margin-bottom: 2px; }
            QListWidget::item:hover { background-color: #1E293B; }
            QListWidget::item:selected { background-color: #06B6D4; color: #020617; font-weight: bold; }
            QLineEdit, QComboBox { background-color: #020617; border: 1px solid #334155; border-radius: 4px; padding: 6px; color: #F8FAFC; }
            QPushButton { background-color: #1E293B; border: 1px solid #334155; border-radius: 4px; padding: 6px 10px; color: #E2E8F0; }
            QPushButton:hover { background-color: #334155; color: #38BDF8; border-color: #38BDF8; }
            QPushButton:checked { background-color: #06B6D4; color: #020617; font-weight: bold; }
            QGroupBox { border: 1px solid #1E293B; border-radius: 6px; margin-top: 10px; padding-top: 10px; font-weight: bold; color: #06B6D4; }
            QStatusBar { background-color: #0F172A; border-top: 1px solid #1E293B; color: #94A3B8; font-size: 11px; }
        """)

        self.db = {}
        self.all_models = []
        self.load_database(db_path)

        # Central Layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left Sidebar (Model Browser)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(4, 4, 4, 4)

        header_lbl = QLabel("▶ FALCON 3.0 ASSETS")
        header_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #10B981; letter-spacing: 1px;")
        sidebar_layout.addWidget(header_lbl)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search models...")
        self.search_input.textChanged.connect(self.filter_models)
        sidebar_layout.addWidget(self.search_input)

        # Category Filter Combo
        self.cat_combo = QComboBox()
        self.cat_combo.addItems([
            "All Categories",
            "Flyable Aircraft",
            "Aircraft",
            "Ground Vehicle",
            "Naval Unit",
            "Terrain Structure",
            "Road & River Ribbon"
        ])
        self.cat_combo.currentTextChanged.connect(self.filter_models)
        sidebar_layout.addWidget(self.cat_combo)

        # Model List
        self.model_list = QListWidget()
        self.model_list.currentItemChanged.connect(self.on_model_selected)
        sidebar_layout.addWidget(self.model_list)

        sidebar.setMaximumWidth(320)
        splitter.addWidget(sidebar)

        # Right Viewport Area
        viewport_container = QWidget()
        viewport_layout = QVBoxLayout(viewport_container)
        viewport_layout.setContentsMargins(4, 4, 4, 4)

        # Top Control Toolbar
        toolbar = QWidget()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(0, 0, 0, 4)

        # Shading mode buttons
        self.btn_solid = QPushButton("Solid Shaded")
        self.btn_wire = QPushButton("Wireframe")
        self.btn_both = QPushButton("Both")
        self.btn_both.setStyleSheet("background-color: #06B6D4; color: #020617; font-weight: bold;")
        self.btn_solid.clicked.connect(lambda: self.set_render_mode('shaded'))
        self.btn_wire.clicked.connect(lambda: self.set_render_mode('wire'))
        self.btn_both.clicked.connect(lambda: self.set_render_mode('both'))
        tb_layout.addWidget(self.btn_solid)
        tb_layout.addWidget(self.btn_wire)
        tb_layout.addWidget(self.btn_both)

        tb_layout.addSpacing(12)

        # View Presets
        btn_iso = QPushButton("Iso")
        btn_front = QPushButton("Front")
        btn_side = QPushButton("Side")
        btn_top = QPushButton("Top")
        btn_iso.clicked.connect(lambda: self.gl_widget.set_view_preset('iso'))
        btn_front.clicked.connect(lambda: self.gl_widget.set_view_preset('front'))
        btn_side.clicked.connect(lambda: self.gl_widget.set_view_preset('side'))
        btn_top.clicked.connect(lambda: self.gl_widget.set_view_preset('top'))
        tb_layout.addWidget(btn_iso)
        tb_layout.addWidget(btn_front)
        tb_layout.addWidget(btn_side)
        tb_layout.addWidget(btn_top)

        tb_layout.addSpacing(12)

        # Auto-rotate toggle
        self.btn_rot = QPushButton("Auto-Rotate")
        self.btn_rot.setCheckable(True)
        self.btn_rot.clicked.connect(lambda: self.gl_widget.set_auto_rotate(self.btn_rot.isChecked()))
        tb_layout.addWidget(self.btn_rot)

        # Grid toggle
        self.btn_grid = QPushButton("Grid")
        self.btn_grid.setCheckable(True)
        self.btn_grid.setChecked(True)
        self.btn_grid.clicked.connect(lambda: self.gl_widget.set_show_grid(self.btn_grid.isChecked()))
        tb_layout.addWidget(self.btn_grid)

        # Reset button
        btn_reset = QPushButton("Reset View")
        btn_reset.clicked.connect(lambda: self.gl_widget.reset_view())
        tb_layout.addWidget(btn_reset)

        tb_layout.addStretch()
        viewport_layout.addWidget(toolbar)

        # 3D OpenGL / Canvas Widget
        self.gl_widget = Model3DWidget()
        if self.db.get('metadata', {}).get('palette'):
            self.gl_widget.set_palette(self.db['metadata']['palette'])
        viewport_layout.addWidget(self.gl_widget, 1)

        splitter.addWidget(viewport_container)
        splitter.setStretchFactor(1, 4)

        # Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready. Select an asset to inspect 3D geometry.")

        # Populate list
        self.filter_models()
        if self.model_list.count() > 0:
            self.model_list.setCurrentRow(0)

    def set_render_mode(self, mode):
        self.gl_widget.set_render_mode(mode)
        self.btn_solid.setStyleSheet("background-color: #06B6D4; color: #020617; font-weight: bold;" if mode == 'shaded' else "")
        self.btn_wire.setStyleSheet("background-color: #06B6D4; color: #020617; font-weight: bold;" if mode == 'wire' else "")
        self.btn_both.setStyleSheet("background-color: #06B6D4; color: #020617; font-weight: bold;" if mode == 'both' else "")

    def load_database(self, db_path):
        p = Path(db_path)
        if not p.exists():
            print(f"Database {db_path} missing. Running extract_all_3d_assets.py...")
            import subprocess
            subprocess.run([sys.executable, 'scripts/extract_all_3d_assets.py'], check=True)

        with open(p, 'rb') as f:
            self.db = json.load(f)

        self.all_models = []
        for m in self.db.get('flyable_aircraft', []):
            m['category'] = 'Flyable Aircraft'
            self.all_models.push(m) if hasattr(self.all_models, 'push') else self.all_models.append(m)
        for m in self.db.get('vehicles_and_units', []):
            self.all_models.append(m)
        for m in self.db.get('terrain_structures', []):
            self.all_models.append(m)

    def filter_models(self):
        query = self.search_input.text().lower().strip()
        cat = self.cat_combo.currentText()

        self.model_list.clear()
        for m in self.all_models:
            m_cat = m.get('category', 'Generic')
            if cat != "All Categories" and m_cat != cat:
                continue
            name = m.get('name', '')
            if query and query not in name.lower() and query not in m_cat.lower():
                continue

            vc = m.get('vertex_count', 0)
            fc = m.get('face_count', 0)
            ec = m.get('edge_count', 0)
            label = f"{name:20s} ({vc}v, {fc or ec}p)"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, m)
            self.model_list.addItem(item)

    def on_model_selected(self, current, previous):
        if not current: return
        model = current.data(Qt.ItemDataRole.UserRole)
        if not model: return

        self.gl_widget.set_model(model)
        name = model.get('name', 'Unknown')
        cat = model.get('category', 'Generic')
        vc = model.get('vertex_count', 0)
        fc = model.get('face_count', 0)
        ec = model.get('edge_count', 0)
        src = model.get('source', '')
        self.status.showMessage(f"Asset: {name} | Category: {cat} | Vertices: {vc} | Faces: {fc} | Edges: {ec} | Source: {src}")

def main():
    app = QApplication(sys.argv)
    win = Falcon3DViewerWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
