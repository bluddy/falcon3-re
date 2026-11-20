import json

with open('analysis/viewer/assets_database.json') as f:
    db = json.load(f)

obj_f16 = [o for o in db['vehicles_and_units'] if o['name'] == 'F16'][0]
rep_f16 = [o for o in db.get('tactical_reference', []) if 'F-16' in o.get('name','') or 'F16' in o.get('name','')][0]
bin_f16 = db['flyable_aircraft'][0]

print("F-16 comparisons:")
print(f"OBJECTS F-16: {obj_f16['vertex_count']}v, {obj_f16['face_count']}f, lods={len(obj_f16['lods'])}")
for i, l in enumerate(obj_f16['lods']):
    print(f"  LOD {i}: {l['vertex_count']}v, {l['face_count']}f")

print(f"REPORT.DAT F-16: {rep_f16['vertex_count']}v, {rep_f16['face_count']}f")
for i, l in enumerate(rep_f16.get('lods', [])):
    print(f"  LOD {i}: {l['vertex_count']}v, {l['face_count']}f")

print(f"FALCOBJ.BIN F-16: {bin_f16['vertex_count']}v, {bin_f16['face_count']}f")
