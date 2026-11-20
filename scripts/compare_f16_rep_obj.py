import json

data = json.load(open('analysis/viewer/assets_database.json'))
rep_f16 = [x for x in data['tactical_reference'] if 'F-16' in x['name'].upper() or 'F16' in x['name'].upper()][0]
obj_f16 = [x for x in data['vehicles_and_units'] if x['name'].upper() == 'F16'][0]

print("=== F-16 Comparison ===")
print("REPORT.DAT F-16:", len(rep_f16['vertices']), "verts,", len(rep_f16['faces']), "faces")
print("OBJECTS F-16:", len(obj_f16['vertices']), "verts,", len(obj_f16['faces']), "faces")

# Let's inspect LOD 0 verts in OBJECTS F-16 vs REPORT.DAT F-16
print("\nFirst 10 vertices:")
print("Idx | REPORT.DAT (x, y, z)          | OBJECTS (x, y, z)")
print("----+-------------------------------+-------------------------------")
for i in range(10):
    rv = rep_f16['vertices'][i]
    ov = obj_f16['vertices'][i]
    print(f" {i:2d} | ({rv[0]:6.2f}, {rv[1]:6.2f}, {rv[2]:6.2f}) | ({ov[0]:6.2f}, {ov[1]:6.2f}, {ov[2]:6.2f})")
