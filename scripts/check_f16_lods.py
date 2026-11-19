import json

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

for obj in db['vehicles_and_units']:
    if 'F16' in obj['name']:
        f16 = obj
        break

print("Top-level: verts =", len(f16['vertices']), "faces =", len(f16['faces']), "edges =", len(f16['edges']))
for l in f16.get('lods', []):
    print(f"LOD {l['lod']}: verts = {len(l['vertices'])}, faces = {len(l['faces'])}, edges = {len(l['edges'])}")
