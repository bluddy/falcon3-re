"""
Falcon 3.0 — Native Qt6 3D Asset & Object Inspector
Visualizes all flight engine assets (Aircraft, Vehicles, Ground Structures, Ribbons)
Features:
- Polygon Inspector: Select & inspect individual faces by index
- 3D Polygon Number Labels: Overlay face numbers at centroids
- 3D Vertex Number Labels: Overlay vertex numbers at vertices
- Backface Culling toggle (authentic Falcon 3.0 behavior)
- LOD Selector (LOD 0, 1, 2, 3)
- Shading modes: Solid Shaded, Wireframe, Both
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
    QLabel, QGroupBox, QSplitter, QStatusBar, QFrame, QCheckBox
)

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
        self.cull_backfaces = False
        self.show_poly_numbers = False
        self.show_vert_numbers = False
        self.selected_face_idx = None # Highlight specific face
        
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
        self.timer.start(16)

        # Geometry data
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
        self.selected_face_idx = None
        self.prepare_geometry()
        self.update()

    def set_selected_face(self, f_idx):
        self.selected_face_idx = f_idx
        self.update()

    def set_render_mode(self, mode):
        self.render_mode = mode
        self.update()

    def set_show_grid(self, val):
        self.show_grid = val
        self.update()

    def set_cull_backfaces(self, val):
        self.cull_backfaces = val
        self.update()

    def set_show_poly_numbers(self, val):
        self.show_poly_numbers = val
        self.update()

    def set_show_vert_numbers(self, val):
        self.show_vert_numbers = val
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
        elif preset == 'back':
            self.rot_x = 0.0
            self.rot_y = 180.0
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

        lods = self.model.get('lods', [])
        if lods and self.lod_idx < len(lods):
            lod = lods[self.lod_idx]
            if lod and lod.get('vertices'):
                verts = lod.get('vertices', verts)
                faces = lod.get('faces', faces)
                edges = lod.get('edges', edges)

        if not verts:
            self.centered_verts = []
            self.faces = []
            self.edges = []
            return

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

    if HAS_OPENGL:
        def initializeGL(self):
            gl.glClearColor(0.04, 0.06, 0.09, 1.0)
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glEnable(gl.GL_COLOR_MATERIAL)
            gl.glEnable(gl.GL_LIGHTING)
            gl.glEnable(gl.GL_LIGHT0)
            gl.glEnable(gl.GL_NORMALIZE)
            gl.glShadeModel(gl.GL_SMOOTH)

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

            # Backface culling state
            if self.cull_backfaces:
                gl.glEnable(gl.GL_CULL_FACE)
                gl.glCullFace(gl.GL_BACK)
                gl.glLightModeli(gl.GL_LIGHT_MODEL_TWO_SIDE, gl.GL_FALSE)
            else:
                gl.glDisable(gl.GL_CULL_FACE)
                gl.glLightModeli(gl.GL_LIGHT_MODEL_TWO_SIDE, gl.GL_TRUE)

            # Ground Grid
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

            # Render Solid Faces
            if self.faces and self.render_mode in ('shaded', 'both'):
                gl.glEnable(gl.GL_LIGHTING)
                gl.glEnable(gl.GL_POLYGON_OFFSET_FILL)
                gl.glPolygonOffset(1.0, 1.0)
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

                for f_idx, f in enumerate(self.faces):
                    ring = f.get('indices', [])
                    if len(ring) < 3: continue

                    is_highlighted = (self.selected_face_idx == f_idx)
                    col_idx = f.get('color', 142)
                    rgb = [160, 160, 160]
                    if self.palette and col_idx < len(self.palette):
                        rgb = self.palette[col_idx]

                    if is_highlighted:
                        # Bright yellow highlight
                        gl.glColor3f(1.0, 0.9, 0.0)
                    else:
                        gl.glColor3f(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)

                    # Compute normal
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

                    # Render via triangle fan for robust non-convex handling
                    gl.glBegin(gl.GL_TRIANGLE_FAN)
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
                    gl.glColor3f(0.0, 1.0, 0.4)
                else:
                    gl.glColor3f(0.1, 0.8, 1.0)

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

            # Render Highlighted Face Outline in Magenta
            if self.selected_face_idx is not None and self.selected_face_idx < len(self.faces):
                gl.glDisable(gl.GL_LIGHTING)
                gl.glLineWidth(3.0)
                gl.glColor3f(1.0, 0.2, 0.8)
                ring = self.faces[self.selected_face_idx].get('indices', [])
                gl.glBegin(gl.GL_LINE_LOOP)
                for vi in ring:
                    if vi < len(self.centered_verts):
                        vx, vy, vz = self.centered_verts[vi]
                        gl.glVertex3f(vx, vy, vz)
                gl.glEnd()

            # 2D Screen Overlays for Face & Vertex Numbers
            if self.show_poly_numbers or self.show_vert_numbers:
                self.render_labels_overlay()

        def render_labels_overlay(self):
            # Project 3D points to 2D window coordinates using QPainter
            modelview = gl.glGetDoublev(gl.GL_MODELVIEW_MATRIX)
            projection = gl.glGetDoublev(gl.GL_PROJECTION_MATRIX)
            viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)

            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

            font = QtGui.QFont("Arial", 8, QtGui.QFont.Weight.Bold)
            painter.setFont(font)

            # Draw polygon number labels at face centroids
            if self.show_poly_numbers and self.faces:
                for f_idx, f in enumerate(self.faces):
                    ring = f.get('indices', [])
                    if len(ring) < 3: continue
                    pts = [self.centered_verts[vi] for vi in ring if vi < len(self.centered_verts)]
                    if not pts: continue
                    cx = sum(p[0] for p in pts) / len(pts)
                    cy = sum(p[1] for p in pts) / len(pts)
                    cz = sum(p[2] for p in pts) / len(pts)

                    win_pos = glu.gluProject(cx, cy, cz, modelview, projection, viewport)
                    if win_pos and win_pos[2] < 1.0: # In front of camera
                        sx = win_pos[0]
                        sy = viewport[3] - win_pos[1] # Flip Y for Qt
                        is_sel = (self.selected_face_idx == f_idx)
                        bg_col = QtGui.QColor(255, 220, 0, 220) if is_sel else QtGui.QColor(15, 23, 42, 190)
                        txt_col = QtGui.QColor(0, 0, 0) if is_sel else QtGui.QColor(56, 189, 248)
                        txt = f"#{f_idx}"

                        rect = painter.fontMetrics().boundingRect(txt)
                        rect.adjust(-3, -2, 3, 2)
                        rect.moveCenter(QPoint(int(sx), int(sy)))
                        painter.fillRect(rect, bg_col)
                        painter.setPen(QtGui.QPen(txt_col))
                        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, txt)

            # Draw vertex number labels
            if self.show_vert_numbers and self.centered_verts:
                painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
                for vi, p in enumerate(self.centered_verts):
                    win_pos = glu.gluProject(p[0], p[1], p[2], modelview, projection, viewport)
                    if win_pos and win_pos[2] < 1.0:
                        sx = win_pos[0]
                        sy = viewport[3] - win_pos[1]
                        txt = f"{vi}"
                        painter.drawText(int(sx) + 4, int(sy) - 4, txt)

            painter.end()


class Falcon3DViewerWindow(QMainWindow):
    def __init__(self, db_path='analysis/viewer/assets_database.json'):
        super().__init__()
        self.setWindowTitle("Falcon 3.0 — 3D Asset & Object Inspector (Qt6)")
        self.resize(1380, 850)
        self.setStyleSheet("""
            QMainWindow { background-color: #0A0E17; }
            QWidget { color: #F1F5F9; font-family: monospace, sans-serif; font-size: 12px; }
            QListWidget { background-color: #0F172A; border: 1px solid #1E293B; border-radius: 4px; padding: 4px; }
            QListWidget::item { padding: 4px 6px; border-radius: 4px; margin-bottom: 2px; }
            QListWidget::item:hover { background-color: #1E293B; }
            QListWidget::item:selected { background-color: #06B6D4; color: #020617; font-weight: bold; }
            QLineEdit, QComboBox { background-color: #020617; border: 1px solid #334155; border-radius: 4px; padding: 5px; color: #F8FAFC; }
            QPushButton { background-color: #1E293B; border: 1px solid #334155; border-radius: 4px; padding: 5px 8px; color: #E2E8F0; }
            QPushButton:hover { background-color: #334155; color: #38BDF8; border-color: #38BDF8; }
            QPushButton:checked { background-color: #06B6D4; color: #020617; font-weight: bold; }
            QCheckBox { color: #E2E8F0; font-weight: bold; spacing: 5px; }
            QCheckBox::indicator { width: 14px; height: 14px; }
            QGroupBox { border: 1px solid #1E293B; border-radius: 6px; margin-top: 10px; padding-top: 10px; font-weight: bold; color: #06B6D4; }
            QStatusBar { background-color: #0F172A; border-top: 1px solid #1E293B; color: #94A3B8; font-size: 11px; }
        """)

        self.db = {}
        self.all_models = []
        self.current_model = None
        self.load_database(db_path)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ---------------- Left Sidebar (Model Browser) ----------------
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(4, 4, 4, 4)

        header_lbl = QLabel("▶ FALCON 3.0 ASSETS")
        header_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #10B981; letter-spacing: 1px;")
        sidebar_layout.addWidget(header_lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search name, category, source...")
        self.search_input.textChanged.connect(self.filter_models)
        sidebar_layout.addWidget(self.search_input)

        self.src_combo = QComboBox()
        self.src_combo.addItems([
            "All Sources",
            "REPORT.DAT (Tactical Dossiers)",
            "OBJECTS (In-Flight Models)",
            "*OBJ.BIN (Flyable High-LOD)",
            "MAPOBJ (Terrain Structures)"
        ])
        self.src_combo.currentTextChanged.connect(self.filter_models)
        sidebar_layout.addWidget(self.src_combo)

        self.cat_combo = QComboBox()
        self.cat_combo.addItems([
            "All Categories",
            "Flyable Aircraft",
            "Aircraft",
            "Ground Vehicle",
            "Naval Unit",
            "Air Defense",
            "Terrain Structure",
            "Road & River Ribbon",
            "Tactical Reference"
        ])
        self.cat_combo.currentTextChanged.connect(self.filter_models)
        sidebar_layout.addWidget(self.cat_combo)

        self.model_list = QListWidget()
        self.model_list.currentItemChanged.connect(self.on_model_selected)
        sidebar_layout.addWidget(self.model_list)

        sidebar.setMinimumWidth(260)
        sidebar.setMaximumWidth(340)
        splitter.addWidget(sidebar)

        # ---------------- Center Viewport Area ----------------
        viewport_container = QWidget()
        viewport_layout = QVBoxLayout(viewport_container)
        viewport_layout.setContentsMargins(4, 4, 4, 4)

        # Top Control Toolbar
        toolbar = QWidget()
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(0, 0, 0, 4)

        self.btn_solid = QPushButton("Solid")
        self.btn_wire = QPushButton("Wire")
        self.btn_both = QPushButton("Both")
        self.btn_both.setStyleSheet("background-color: #06B6D4; color: #020617; font-weight: bold;")
        self.btn_solid.clicked.connect(lambda: self.set_render_mode('shaded'))
        self.btn_wire.clicked.connect(lambda: self.set_render_mode('wire'))
        self.btn_both.clicked.connect(lambda: self.set_render_mode('both'))
        tb_layout.addWidget(self.btn_solid)
        tb_layout.addWidget(self.btn_wire)
        tb_layout.addWidget(self.btn_both)

        tb_layout.addSpacing(8)

        # LOD Selector
        tb_layout.addWidget(QLabel("LOD:"))
        self.lod_combo = QComboBox()
        self.lod_combo.addItems(["LOD 0", "LOD 1", "LOD 2", "LOD 3"])
        self.lod_combo.currentIndexChanged.connect(self.on_lod_changed)
        tb_layout.addWidget(self.lod_combo)

        tb_layout.addSpacing(8)

        # View Presets
        for p in ["Iso", "Front", "Side", "Top", "Back"]:
            b = QPushButton(p)
            b.clicked.connect(lambda ch, pres=p.lower(): self.gl_widget.set_view_preset(pres))
            tb_layout.addWidget(b)

        tb_layout.addSpacing(8)

        # Toggles
        self.chk_cull = QCheckBox("Cull Back")
        self.chk_cull.setChecked(False)
        self.chk_cull.toggled.connect(lambda val: self.gl_widget.set_cull_backfaces(val))
        tb_layout.addWidget(self.chk_cull)

        self.chk_poly_nums = QCheckBox("Poly IDs")
        self.chk_poly_nums.setChecked(False)
        self.chk_poly_nums.toggled.connect(lambda val: self.gl_widget.set_show_poly_numbers(val))
        tb_layout.addWidget(self.chk_poly_nums)

        self.chk_vert_nums = QCheckBox("Vert IDs")
        self.chk_vert_nums.setChecked(False)
        self.chk_vert_nums.toggled.connect(lambda val: self.gl_widget.set_show_vert_numbers(val))
        tb_layout.addWidget(self.chk_vert_nums)

        btn_reset = QPushButton("Reset")
        btn_reset.clicked.connect(lambda: self.gl_widget.reset_view())
        tb_layout.addWidget(btn_reset)

        tb_layout.addStretch()
        viewport_layout.addWidget(toolbar)

        # 3D OpenGL Widget
        self.gl_widget = Model3DWidget()
        if self.db.get('metadata', {}).get('palette'):
            self.gl_widget.set_palette(self.db['metadata']['palette'])
        viewport_layout.addWidget(self.gl_widget, 1)

        splitter.addWidget(viewport_container)
        splitter.setStretchFactor(1, 4)

        # ---------------- Right Sidebar (Polygon Inspector) ----------------
        poly_panel = QWidget()
        poly_layout = QVBoxLayout(poly_panel)
        poly_layout.setContentsMargins(4, 4, 4, 4)

        poly_lbl = QLabel("▶ POLYGON INSPECTOR")
        poly_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #38BDF8; letter-spacing: 1px;")
        poly_layout.addWidget(poly_lbl)

        # Tactical Reference Specs Box
        self.specs_box = QGroupBox("DOSSIER SPECIFICATIONS")
        self.specs_box_layout = QVBoxLayout(self.specs_box)
        self.specs_lbl = QLabel("Select Tactical Reference asset to view specifications.")
        self.specs_lbl.setWordWrap(True)
        self.specs_lbl.setStyleSheet("color: #E2E8F0; font-size: 11px;")
        self.specs_box_layout.addWidget(self.specs_lbl)
        self.specs_box.setVisible(False)
        poly_layout.addWidget(self.specs_box)

        self.poly_summary_lbl = QLabel("Select face to inspect")
        self.poly_summary_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")
        poly_layout.addWidget(self.poly_summary_lbl)

        self.face_list = QListWidget()
        self.face_list.currentItemChanged.connect(self.on_face_selected)
        poly_layout.addWidget(self.face_list)

        self.face_detail_lbl = QLabel("")
        self.face_detail_lbl.setWordWrap(True)
        self.face_detail_lbl.setStyleSheet("background-color: #0F172A; border: 1px solid #1E293B; border-radius: 4px; padding: 6px; font-size: 11px;")
        poly_layout.addWidget(self.face_detail_lbl)

        poly_panel.setMaximumWidth(320)
        splitter.addWidget(poly_panel)
        splitter.setStretchFactor(2, 1)

        # Status Bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready. Select an asset to inspect 3D geometry.")

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
            import subprocess
            subprocess.run([sys.executable, 'scripts/extract_all_3d_assets.py'], check=True)

        with open(p, 'rb') as f:
            self.db = json.load(f)

        self.all_models = []
        for m in self.db.get('flyable_aircraft', []):
            m['category'] = 'Flyable Aircraft'
            self.all_models.append(m)
        for m in self.db.get('vehicles_and_units', []):
            self.all_models.append(m)
        for m in self.db.get('terrain_structures', []):
            self.all_models.append(m)
        for m in self.db.get('tactical_reference', []):
            self.all_models.append(m)

    def filter_models(self):
        query = self.search_input.text().lower().strip()
        norm_query = query.replace('-', '').replace(' ', '').replace('_', '')
        cat = self.cat_combo.currentText()
        src_selection = self.src_combo.currentText()

        src_mapping = {
            "REPORT.DAT (Tactical Dossiers)": "REPORT.DAT",
            "OBJECTS (In-Flight Models)": "OBJECTS",
            "*OBJ.BIN (Flyable High-LOD)": "AIRCRAFT_BIN",
            "MAPOBJ (Terrain Structures)": "MAPOBJ"
        }
        target_src = src_mapping.get(src_selection, None)

        self.model_list.clear()
        for m in self.all_models:
            m_src = m.get('source', '')
            if target_src and m_src != target_src:
                continue

            m_cat = m.get('category', 'Generic')
            if cat != "All Categories":
                if cat == "Tactical Reference":
                    if m_src != 'REPORT.DAT' and m_cat != 'Tactical Reference':
                        continue
                elif cat == "Terrain Structure":
                    if m_cat not in ['Terrain Structure', 'Structure']:
                        continue
                elif m_cat != cat:
                    continue

            name = m.get('name', '')
            sub_cat = m.get('sub_category', '')
            if query:
                searchable = f"{name} {m_cat} {sub_cat} {m_src}".lower()
                norm_searchable = searchable.replace('-', '').replace(' ', '').replace('_', '')
                if query not in searchable and norm_query not in norm_searchable:
                    continue

            vc = m.get('vertex_count', 0)
            fc = m.get('face_count', 0)
            ec = m.get('edge_count', 0)

            src_tag = {
                'REPORT.DAT': '[REP]',
                'OBJECTS': '[OBJ]',
                'AIRCRAFT_BIN': '[BIN]',
                'MAPOBJ': '[MAP]'
            }.get(m_src, '[---]')

            label = f"{src_tag} {name:18s} ({vc}v, {fc or ec}p)"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, m)
            self.model_list.addItem(item)

    def on_model_selected(self, current, previous):
        if not current: return
        model = current.data(Qt.ItemDataRole.UserRole)
        if not model: return

        self.current_model = model
        
        # If model has LODs and LOD 2 is high-detail, default to LOD 2
        lods = model.get('lods', [])
        if len(lods) > 2 and lods[2] and lods[2].get('vertices'):
            self.lod_combo.blockSignals(True)
            self.lod_combo.setCurrentIndex(2)
            self.lod_combo.blockSignals(False)
            lod = 2
        else:
            self.lod_combo.blockSignals(True)
            self.lod_combo.setCurrentIndex(0)
            self.lod_combo.blockSignals(False)
            lod = 0

        self.gl_widget.set_model(model, lod)
        self.populate_face_list()

        # Update Dossier Specifications if available
        specs = model.get('specs', [])
        if specs:
            specs_text = "\n".join(specs[:8])
            sub_cat = model.get('sub_category', '')
            self.specs_box.setTitle(f"DOSSIER: {sub_cat.upper()}" if sub_cat else "DOSSIER SPECIFICATIONS")
            self.specs_lbl.setText(specs_text)
            self.specs_box.setVisible(True)
        else:
            self.specs_box.setVisible(False)

        name = model.get('name', 'Unknown')
        cat = model.get('category', 'Generic')
        vc = model.get('vertex_count', 0)
        fc = model.get('face_count', 0)
        ec = model.get('edge_count', 0)
        src = model.get('source', '')
        self.status.showMessage(f"Asset: {name} | Category: {cat} | Vertices: {vc} | Faces: {fc} | Edges: {ec} | Source: {src}")

    def on_lod_changed(self, idx):
        if self.current_model:
            self.gl_widget.set_model(self.current_model, idx)
            self.populate_face_list()

    def populate_face_list(self):
        self.face_list.clear()
        faces = self.gl_widget.faces
        self.poly_summary_lbl.setText(f"Total Faces in View: {len(faces)}")

        for f_idx, f in enumerate(faces):
            ring = f.get('indices', [])
            col = f.get('color', 0)
            cnt = len(ring)
            txt = f"Face #{f_idx:02d}: col={col:3d} ({cnt} verts) -> {ring}"
            item = QListWidgetItem(txt)
            item.setData(Qt.ItemDataRole.UserRole, f_idx)
            self.face_list.addItem(item)

    def on_face_selected(self, current, previous):
        if not current:
            self.gl_widget.set_selected_face(None)
            self.face_detail_lbl.setText("")
            return
        f_idx = current.data(Qt.ItemDataRole.UserRole)
        self.gl_widget.set_selected_face(f_idx)

        faces = self.gl_widget.faces
        verts = self.gl_widget.centered_verts
        if f_idx < len(faces):
            f = faces[f_idx]
            ring = f.get('indices', [])
            col = f.get('color', 0)
            coords_str = "\n".join(f"  v{vi:02d}: {verts[vi]}" for vi in ring if vi < len(verts))
            self.face_detail_lbl.setText(
                f"Selected Face #{f_idx}\n"
                f"Color Index: {col}\n"
                f"Vertices ({len(ring)}):\n{coords_str}"
            )


def main():
    app = QApplication(sys.argv)
    win = Falcon3DViewerWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
