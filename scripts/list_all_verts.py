import json

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

for obj in db['vehicles_and_units']:
    if 'F16' in obj['name']:
        f16 = obj
        break

verts = f16['vertices']
print("F16 Vertices (X, Y, Z in GL coordinates):")
for i, v in enumerate(verts):
    # Remember: GL coordinates were [Y_falcon/10, -Z_falcon/10, -X_falcon/10]
    # So v[0] = lateral (starboard/port wing), v[1] = vertical (height), v[2] = longitudinal (-X_falcon, forward/aft)
    print(f"v{i:02d}: x={v[0]:6.1f}, y={v[1]:6.1f}, z={v[2]:6.1f}")
