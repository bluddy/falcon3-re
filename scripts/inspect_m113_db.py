import json

data = json.load(open('analysis/viewer/assets_database.json'))
rep_m113 = [x for x in data['tactical_reference'] if '113' in x['name'].upper()][0]
obj_m113 = [x for x in data['vehicles_and_units'] if '113' in x['name'].upper()][0]

print('REPORT M113:', rep_m113['name'])
print('  Verts:', len(rep_m113['vertices']))
print('  Faces:', len(rep_m113['faces']))
for idx, f in enumerate(rep_m113['faces']):
    print(f'   f{idx:02d}: color={f["color"]}, indices={f["indices"]}')

print('\nOBJECTS M113:', obj_m113['name'])
print('  Verts:', len(obj_m113['vertices']))
print('  Faces:', len(obj_m113['faces']))
for idx, f in enumerate(obj_m113['faces']):
    print(f'   f{idx:02d}: color={f["color"]}, indices={f["indices"]}')
