import json
import math

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

for obj in db['vehicles_and_units']:
    if 'F16' in obj['name']:
        f16 = obj
        break

verts = f16['vertices']
faces = f16['faces']

def cross(a, b):
    return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]

def sub(a, b):
    return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]

for f_idx in [38, 39, 44, 45, 50, 51, 52]:
    face = faces[f_idx]
    ring = face['indices']
    pts = [verts[i] for i in ring]
    print(f"\nFace {f_idx} (col={face['color']}, len={len(ring)}): {ring}")
    for idx, p in zip(ring, pts):
        print(f"  v{idx:02d}: {p}")
    v0, v1, v2 = pts[0], pts[1], pts[2]
    n = cross(sub(v1, v0), sub(v2, v0))
    l = math.sqrt(n[0]*n[0] + n[1]*n[1] + n[2]*n[2])
    if l > 0:
        norm = [round(n[0]/l, 3), round(n[1]/l, 3), round(n[2]/l, 3)]
        print(f"  Normal: {norm}")
