import json
import math

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = None
for cat in ['flyable_aircraft', 'vehicles_and_units']:
    for m in db[cat]:
        if 'F16' in m['name']:
            f16 = m
            break
    if f16:
        break

if not f16:
    print("F16 not found!")
    exit()

verts = f16['vertices']
faces = f16['faces']
print(f"F-16 Model: {len(verts)} vertices, {len(faces)} faces\n")

def vec_sub(a, b):
    return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]

def cross(a, b):
    return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]

def dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def mag(a):
    return math.sqrt(dot(a, a))

warped_count = 0
for fi, f in enumerate(faces):
    idxs = f['indices']
    f_verts = [verts[i] for i in idxs]
    n = len(idxs)
    
    max_dist = 0.0
    if n >= 4:
        # best-fit or first 3
        p0, p1, p2 = f_verts[0], f_verts[1], f_verts[2]
        v1 = vec_sub(p1, p0)
        v2 = vec_sub(p2, p0)
        normal = cross(v1, v2)
        m = mag(normal)
        if m > 1e-4:
            unit_n = [x/m for x in normal]
            for v in f_verts[3:]:
                dist = abs(dot(vec_sub(v, p0), unit_n))
                if dist > max_dist:
                    max_dist = dist
                    
    xs = [v[0] for v in f_verts]
    ys = [v[1] for v in f_verts]
    zs = [v[2] for v in f_verts]
    
    status = ""
    if max_dist > 1.0:
        status = f"--> WARPED! non-planar dist = {max_dist:.2f}"
        warped_count += 1
    
    print(f"Face {fi:2d} ({n}-gon, col={f['color']:2d}): idxs={idxs} {status}")
    if status:
        for idx in idxs:
            print(f"       v{idx:02d}: {verts[idx]}")

print(f"\nTotal faces: {len(faces)}, Warped faces: {warped_count}")
