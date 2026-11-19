import json

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

verts = f16['vertices']
for vi in [40, 41, 42, 43, 44, 45, 46, 47, 60, 63, 64, 70, 73]:
    print(f"v{vi:02d}: {verts[vi]}")
