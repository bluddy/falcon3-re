import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

data = json.load(open('analysis/viewer/assets_database.json'))
rep_m113 = [x for x in data['tactical_reference'] if '113' in x['name'].upper()][0]
obj_m113 = [x for x in data['vehicles_and_units'] if '113' in x['name'].upper()][0]

fig = plt.figure(figsize=(16, 8))

# 1. REPORT.DAT M113
ax1 = fig.add_subplot(121, projection='3d')
verts_r = rep_m113['vertices']
faces_r = rep_m113['faces']
polys_r = []
for f in faces_r:
    poly = [verts_r[idx] for idx in f['indices']]
    polys_r.append(poly)
coll_r = Poly3DCollection(polys_r, alpha=0.7, edgecolor='k', linewidths=1)
coll_r.set_facecolor([0.4, 0.7, 0.4])
ax1.add_collection3d(coll_r)
ax1.set_title(f"REPORT.DAT M113 ({len(verts_r)}v, {len(faces_r)}f)")
ax1.set_xlim(-20, 20); ax1.set_ylim(-20, 20); ax1.set_zlim(-20, 20)
ax1.set_xlabel('X'); ax1.set_ylabel('Y'); ax1.set_zlabel('Z')

# 2. OBJECTS M113
ax2 = fig.add_subplot(122, projection='3d')
verts_o = obj_m113['vertices']
faces_o = obj_m113['faces']
polys_o = []
for f in faces_o:
    poly = [verts_o[idx] for idx in f['indices']]
    polys_o.append(poly)
coll_o = Poly3DCollection(polys_o, alpha=0.7, edgecolor='k', linewidths=1)
coll_o.set_facecolor([0.4, 0.4, 0.7])
ax2.add_collection3d(coll_o)
ax2.set_title(f"OBJECTS M113 ({len(verts_o)}v, {len(faces_o)}f)")
ax2.set_xlim(-20, 20); ax2.set_ylim(-20, 20); ax2.set_zlim(-20, 20)
ax2.set_xlabel('X'); ax2.set_ylabel('Y'); ax2.set_zlabel('Z')

plt.tight_layout()
plt.savefig('analysis/compare_m113.png', dpi=150)
print("Saved analysis/compare_m113.png")
