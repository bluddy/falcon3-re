import json

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = None
for cat in ['vehicles_and_units', 'flyable_aircraft']:
    for obj in db.get(cat, []):
        if 'F16' in obj.get('name', ''):
            f16 = obj
            break

print('F16 found:', f16 is not None)
print('Vertex count:', len(f16['vertices']))
print('Face count:', len(f16['faces']))
for i, face in enumerate(f16['faces']):
    print(f"Face {i:2d}: col={face['color']:3d}, indices={face['indices']}")
