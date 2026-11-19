import sys
import json

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = [x for x in db['vehicles_and_units'] if 'F16' in x['name']][0]
verts = [list(v) for v in f16['vertices']]

# Collar base vertices: 4, 5, 30, 31, 32, 68, 71
# In GL coordinates, X_falcon = -80 corresponds to GL Z = 8.0.
# Let's align all collar base vertices to GL Z = 8.0:
collar_verts = [4, 5, 30, 31, 32, 68, 71]
for vi in collar_verts:
    verts[vi][2] = 8.0

# Calculate centered coordinates
min_z = min(v[2] for v in verts)
max_z = max(v[2] for v in verts)
cz = (min_z + max_z) / 2.0
centered = [[v[0], v[1], round(v[2] - cz, 2)] for v in verts]

print("=== AFTERBURNER COLLAR FACES (13-19) WITH COLLAR BASE Z = 14.7 ===")
for i in range(13, 20):
    f = f16['faces'][i]
    ring = f['indices']
    col = f['color']
    print(f"\nFace {i} (col={col}):")
    for vi in ring:
        print(f"   vi={vi:2d}: centered={centered[vi]}")
