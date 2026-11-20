import json
data = json.load(open('analysis/viewer/assets_database.json'))
rep_f16 = [x for x in data['tactical_reference'] if 'F-16' in x['name'].upper()][0]
verts = rep_f16['vertices']
for i, f in enumerate(rep_f16['faces']):
    ring = f['indices']
    avg_z = sum(verts[v][2] for v in ring) / len(ring)
    if avg_z < -10.0:
        c = f['color']
        print(f"Face {i}: col={c}, avg_z={avg_z:.1f}, idx={ring}")
