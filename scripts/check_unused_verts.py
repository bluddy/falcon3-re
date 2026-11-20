import json

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = None
for m in db['flyable_aircraft'] + db['vehicles_and_units']:
    if 'F16' in m['name']:
        f16 = m
        break

faces = f16['faces']
used_verts = set()
for fi, f in enumerate(faces):
    for vi in f['indices']:
        used_verts.add(vi)

all_verts = set(range(len(f16['vertices'])))
unused = all_verts - used_verts
print(f"Total vertices: {len(all_verts)}")
print(f"Used vertices: {len(used_verts)}")
print(f"Unused vertices: {sorted(list(unused))}")
