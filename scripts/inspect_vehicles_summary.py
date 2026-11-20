import json

data = json.load(open('analysis/viewer/assets_database.json'))
for obj in data['vehicles_and_units']:
    if obj['id'] in [34, 35, 36, 41, 42, 43]:
        verts = obj['vertices']
        print(f"[{obj['id']:02d}] {obj['name']:8s}: {obj['vertex_count']:2d} verts, {obj['face_count']:2d} faces | "
              f"W={max(v[0] for v in verts)-min(v[0] for v in verts):.1f}, "
              f"H={max(v[1] for v in verts)-min(v[1] for v in verts):.1f}, "
              f"L={max(v[2] for v in verts)-min(v[2] for v in verts):.1f}")
