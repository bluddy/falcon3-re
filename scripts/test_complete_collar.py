import sys
import json

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = [x for x in db['vehicles_and_units'] if 'F16' in x['name']][0]
verts = [list(v) for v in f16['vertices']]

# In GL: GL Z = -X / 10
# X = -115 -> GL Z = 11.5
# X = -80  -> GL Z = 8.0

for vi in [48, 49, 50, 51, 52, 69, 72]:
    verts[vi][2] = 11.5

for vi in [4, 5, 30, 31, 32, 68, 71]:
    verts[vi][2] = 8.0

min_z = min(v[2] for v in verts)
max_z = max(v[2] for v in verts)
cz = (min_z + max_z) / 2.0
centered = [[v[0], v[1], round(v[2] - cz, 2)] for v in verts]

print("=== CHECKING FACES 12 TO 19 ===")
for i in range(12, 20):
    f = f16['faces'][i]
    ring = f['indices']
    z_coords = [centered[vi][2] for vi in ring]
    print(f"Face {i:2d} (col={f['color']:3d}): ring={ring} -> Z values: {z_coords}")
