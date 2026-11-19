import json

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = [x for x in db['vehicles_and_units'] if 'F16' in x['name']][0]
for i, f in enumerate(f16['faces']):
    if any(x in f['indices'] for x in [21, 22, 23, 24, 48, 69, 72]):
        print(f"Face {i:2d}: col={f['color']:3d}, indices={f['indices']}")
