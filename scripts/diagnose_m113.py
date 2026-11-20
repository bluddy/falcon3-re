import json
import math

data = json.load(open('analysis/viewer/assets_database.json'))
rep_m113 = [x for x in data['tactical_reference'] if '113' in x['name'].upper()][0]
obj_m113 = [x for x in data['vehicles_and_units'] if '113' in x['name'].upper()][0]

def analyze_model(name, model):
    verts = model['vertices']
    faces = model['faces']
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]
    print(f"\n==================== {name} ====================")
    print(f"Total vertices: {len(verts)}, faces: {len(faces)}")
    print(f"Bounding Box: X [{min(xs):.2f}, {max(xs):.2f}], "
          f"Y [{min(ys):.2f}, {max(ys):.2f}], "
          f"Z [{min(zs):.2f}, {max(zs):.2f}]")
    print(f"Dimensions (W, H, L): {max(xs)-min(xs):.2f} x "
          f"{max(ys)-min(ys):.2f} x "
          f"{max(zs)-min(zs):.2f}")
    
    for f_idx, f in enumerate(faces):
        idx = f['indices']
        poly = [verts[i] for i in idx]
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        cz = sum(p[2] for p in poly) / len(poly)
        # Normal using first 3 vertices
        v0, v1, v2 = poly[0], poly[1], poly[2]
        d1 = [v1[0]-v0[0], v1[1]-v0[1], v1[2]-v0[2]]
        d2 = [v2[0]-v0[0], v2[1]-v0[1], v2[2]-v0[2]]
        nx = d1[1]*d2[2] - d1[2]*d2[1]
        ny = d1[2]*d2[0] - d1[0]*d2[2]
        nz = d1[0]*d2[1] - d1[1]*d2[0]
        nlen = math.sqrt(nx*nx + ny*ny + nz*nz)
        if nlen > 1e-4:
            un = (nx/nlen, ny/nlen, nz/nlen)
        else:
            un = (0, 0, 0)
        print(f"  Face {f_idx:02d} (col {f['color']:3d}, {len(idx)} verts): indices={idx}")
        print(f"    Center: ({cx:6.2f}, {cy:6.2f}, {cz:6.2f}) | Normal: ({un[0]:5.2f}, {un[1]:5.2f}, {un[2]:5.2f})")

analyze_model("REPORT.DAT M113", rep_m113)
analyze_model("OBJECTS M113", obj_m113)
