import sys
import json
import math

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = [x for x in db['vehicles_and_units'] if 'F16' in x['name']][0]
verts = [list(v) for v in f16['vertices']]

# Apply collar alignment:
for vi in [4, 5, 30, 31, 32, 68, 71]:
    verts[vi][2] = 8.0

min_z = min(v[2] for v in verts)
max_z = max(v[2] for v in verts)
cz = (min_z + max_z) / 2.0
centered = [[v[0], v[1], round(v[2] - cz, 2)] for v in verts]

print("=== CHECKING ALL FACES FOR WARPING / NON-PLANARITY ===")
for i, f in enumerate(f16['faces']):
    ring = f['indices']
    col = f['color']
    pts = [centered[vi] for vi in ring]
    # Check span in Z, X, Y
    z_span = max(p[2] for p in pts) - min(p[2] for p in pts)
    # Check if face is a quad and check non-planarity
    if len(ring) == 4:
        # Vector (1-0) x (2-0) vs (3-0)
        v0, v1, v2, v3 = pts
        d1 = [v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]]
        d2 = [v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]]
        d3 = [v3[0]-v0[0], v3[1]-v0[1], v3[2]-v0[2]]
        cross = [d1[1]*d2[2]-d1[2]*d2[1], d1[2]*d2[0]-d1[0]*d2[2], d1[0]*d2[1]-d1[1]*d2[0]]
        dot = abs(cross[0]*d3[0] + cross[1]*d3[1] + cross[2]*d3[2])
        l_cross = math.sqrt(cross[0]**2 + cross[1]**2 + cross[2]**2)
        non_planarity = dot / (l_cross + 1e-6)
        if non_planarity > 1.0 or z_span > 20.0:
            print(f"Face {i:2d} (col={col}): ring={ring}, z_span={z_span:.1f}, non_planarity={non_planarity:.2f}")
