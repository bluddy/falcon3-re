import json

with open('analysis/viewer/assets_database.json') as f:
    db = json.load(f)

objs = db['vehicles_and_units']
with_faces = [o for o in objs if o['face_count'] > 0]
print(f"Total OBJECTS: {len(objs)}, with valid 3D geometry: {len(with_faces)} / {len(objs)}")

for o in objs:
    name = o['name']
    cat = o['category']
    vc = o['vertex_count']
    fc = o['face_count']
    lods = len(o['lods'])
    status = "OK" if fc > 0 else ("VERTS_ONLY" if vc > 0 else "EMPTY")
    print(f"  [{o['id']:02d}] {name:12s} ({cat:14s}): {vc:3d}v, {fc:2d}f, {lods} LODs [{status}]")
