import json

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = [x for x in db['vehicles_and_units'] if 'F16' in x['name']][0]
for i in range(3, 12):
    f = f16['faces'][i]
    print(f"Face {i:2d} (col={f['color']:3d}): ring={f['indices']}")
