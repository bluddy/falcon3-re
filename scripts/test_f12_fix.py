import json
import math

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

for obj in db['vehicles_and_units']:
    if 'F16' in obj['name']:
        f16 = obj
        break

verts = [list(v) for v in f16['vertices']]
faces = f16['faces']

# Check Face 12 before and after:
print("Face 12 before:")
for vi in faces[12]['indices']:
    print(f"  v{vi:2d}: {verts[vi]}")

# If we fix v48, v69, v72 for the nozzle plane:
# In GL coordinates, GL Z = -X / 10. For X = -115, GL Z = 11.5.
# v48 was [0.0, -1.3, -14.0]. Correct: [0.0, -1.3, 11.5]!
# v69 was [-0.9, -1.0, 8.0]. Correct: [-0.9, -1.0, 11.5]!
# v72 was [0.9, -1.0, 8.0]. Correct: [0.9, -1.0, 11.5]!

print("\nFace 12 with nozzle plane Z=11.5:")
fixed_verts = [list(v) for v in verts]
fixed_verts[48][2] = 11.5
fixed_verts[69][2] = 11.5
fixed_verts[72][2] = 11.5
for vi in faces[12]['indices']:
    print(f"  v{vi:2d}: {fixed_verts[vi]}")
