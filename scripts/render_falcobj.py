import struct
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

# Load FALCOBJ.BIN
with open('game/FALCOBJ.BIN', 'rb') as f:
    d = f.read()

file_start = 10
vo = file_start + 0x198A
to = file_start + 0x0020

# 1. Read 22 vertices of LOD 0
# Falcon NED coordinates:
# X = Lateral (Right), Y = Vertical (Up), Z = Forward
# Let's verify coordinate mapping to standard 3D (X_right, Y_up, Z_fwd):
raw_verts = []
for vi in range(22):
    x, y, z = struct.unpack_from('<hhh', d, vo + vi * 6)
    raw_verts.append((x, y, z))

print(f"Loaded {len(raw_verts)} vertices")

# 2. Read polygons
polys = [
    ([14, 18, 19, 12, 11, 13], 'Wing Delta', '#4a6984'),
    ([16, 0, 15, 10, 1, 17], 'Tail Stabilizers', '#5c82a6'),
    ([3, 13, 11], 'Lower Nose', '#7a9bb8'),
    ([4, 13, 11], 'Upper Canopy Nose', '#3b556e'),
    ([2, 4, 21, 3, 7, 5], 'Centerline Spine', '#2c3e50'),
    ([7, 6, 20, 5], 'Ventral Keel', '#243342'),
    ([21, 8, 11, 10, 15, 13, 9], 'Canopy & Fuselage', '#89a9c4')
]

# Plot from 4 camera angles
fig = plt.figure(figsize=(16, 12), facecolor='#1e1e1e')

views = [
    (221, "Perspective / Isometric View", 25, -45),
    (222, "Top View (Wings & Planform)", 90, -90),
    (223, "Side Profile View", 0, -90),
    (224, "Front View", 0, 0)
]

for subplot_idx, title, elev, azim in views:
    ax = fig.add_subplot(subplot_idx, projection='3d', facecolor='#1e1e1e')
    ax.view_init(elev=elev, azim=azim)
    
    # In raw_verts:
    # x is lateral (wingspan)
    # y is vertical (elevation)
    # z is forward (length: +250 nose, -115 tail)
    
    # For plotting: X = x, Y = z (forward), Z = y (vertical)
    poly_verts = []
    colors = []
    for indices, name, col in polys:
        ring = [(raw_verts[idx][0], raw_verts[idx][2], raw_verts[idx][1]) for idx in indices]
        poly_verts.append(ring)
        colors.append(col)
        
    collection = Poly3DCollection(poly_verts, facecolors=colors, edgecolors='#ffffff', linewidths=1.2, alpha=0.85)
    ax.add_collection3d(collection)
    
    # Plot vertex points
    xs = [v[0] for v in raw_verts]
    ys = [v[2] for v in raw_verts]
    zs = [v[1] for v in raw_verts]
    ax.scatter(xs, ys, zs, color='#00ffcc', s=15, alpha=0.9)
    
    ax.set_xlim(-160, 160)
    ax.set_ylim(-160, 270)
    ax.set_zlim(-120, 120)
    
    ax.set_xlabel('X (Wingspan)', color='#aaaaaa', labelpad=10)
    ax.set_ylabel('Z (Forward/Length)', color='#aaaaaa', labelpad=10)
    ax.set_zlabel('Y (Height)', color='#aaaaaa', labelpad=10)
    
    ax.tick_params(colors='#888888')
    ax.set_title(title, color='#ffffff', fontsize=12, pad=12)
    ax.grid(True, color='#333333', linestyle=':', alpha=0.6)

plt.suptitle("Authentic Falcon 3.0 Player F-16 (FALCOBJ.BIN) - In-Flight Model", color='#00ffcc', fontsize=16, y=0.98)
plt.tight_layout()

out_path = 'analysis/viewer/f16_falcobj_rendered.png'
plt.savefig(out_path, dpi=150, facecolor=fig.get_facecolor(), edgecolor='none')
print(f"Saved render to {out_path}!")
