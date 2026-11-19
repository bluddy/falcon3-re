import json

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = None
for cat in ['vehicles_and_units', 'flyable_aircraft']:
    for obj in db.get(cat, []):
        if 'F16' in obj.get('name', ''):
            f16 = obj
            break

verts = f16['vertices']
indices_of_interest = [40, 41, 42, 43, 44, 45, 46, 47, 64, 70, 73, 34, 35, 36, 37, 38, 39]
for idx in indices_of_interest:
    print(f"Vertex {idx:2d}: {verts[idx]}")
