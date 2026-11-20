import json

data = json.load(open('analysis/viewer/assets_database.json'))
rep_m113 = [x for x in data['tactical_reference'] if '113' in x['name'].upper()][0]
obj_m113 = [x for x in data['vehicles_and_units'] if '113' in x['name'].upper()][0]

print("=== VERTICES 0-13 (Hull) ===")
print("Index | REPORT.DAT (x, y, z)          | OBJECTS (x, y, z)")
print("------+-------------------------------+-------------------------------")
for i in range(14):
    rv = rep_m113['vertices'][i]
    ov = obj_m113['vertices'][i]
    print(f"  v{i:02d} | ({rv[0]:6.2f}, {rv[1]:6.2f}, {rv[2]:6.2f}) | ({ov[0]:6.2f}, {ov[1]:6.2f}, {ov[2]:6.2f})")

print("\n=== VERTICES 14-19 (Part 1 / Cupola) ===")
for i in range(14, len(rep_m113['vertices'])):
    rv = rep_m113['vertices'][i]
    ov = obj_m113['vertices'][i] if i < len(obj_m113['vertices']) else [0, 0, 0]
    print(f"  v{i:02d} | ({rv[0]:6.2f}, {rv[1]:6.2f}, {rv[2]:6.2f}) | ({ov[0]:6.2f}, {ov[1]:6.2f}, {ov[2]:6.2f})")
