import json
import math

with open('analysis/viewer/assets_database.json', 'r') as f:
    db = json.load(f)

f16 = None
for m in db['flyable_aircraft'] + db['vehicles_and_units']:
    if 'F16' in m['name']:
        f16 = m
        break

verts = [list(v) for v in f16['vertices']]

# Let's see: in OpenGL coordinates, verts are [X_gl, Y_gl, Z_gl] = [y/10, -z/10, -x/10].
# Here, X_gl is lateral (starboard is +, port is -).
# Y_gl is vertical (up is +, down is -).
# Z_gl is longitudinal (fwd is -, aft is +).

# If an aircraft is symmetrical, for any starboard vertex with X_gl > 0,
# there should be a matching port vertex with X_gl = -X_gl_stbd, Y_gl = Y_gl_stbd, Z_gl = Z_gl_stbd!

# Let's map our topological pairs:
# pairs of (stbd_vi, port_vi):
topo_pairs = [
    (6, 32),
    (8, 7),
    (11, 14),
    (10, 13),
    (9, 12),
    (8, 15),
    (16, 25),
    (17, 24),
    (20, 23),
    (18, 21),
    (19, 22),
    (43, 46),
    (42, 47),
    (41, 44),
    (73, 70),
    (5, 4),
    (30, 32), # collar
    (63, 60), # ventral
    (71, 68),
    (72, 69),
    (49, 52),
    (50, 51)
]

for s_vi, p_vi in topo_pairs:
    sv = verts[s_vi]
    # port vertex should be [-sv[0], sv[1], sv[2]]
    verts[p_vi] = [-sv[0], sv[1], sv[2]]

# Centerline vertices (y == 0 -> X_gl == 0):
centerline = [0, 2, 3, 26, 27, 28, 29, 31, 33, 40, 45, 48, 64, 65, 66]
for c_vi in centerline:
    verts[c_vi][0] = 0.0

f16['vertices'] = verts

with open('analysis/viewer/assets_database.json', 'w') as f:
    json.dump(db, f)

print("Applied topological symmetry mirroring to assets_database.json")
