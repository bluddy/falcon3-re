import json

db = json.load(open('analysis/viewer/assets_database.json'))
obj_f16 = [m for m in db['vehicles_and_units'] if m['name'] == 'F16'][0]
print(f"OBJECTS F16: {len(obj_f16['vertices'])} verts, {len(obj_f16['faces'])} faces")
for fi, f in enumerate(obj_f16['faces']):
    print(f"Face {fi:02d}: col={f['color']} ring={f['indices']}")
