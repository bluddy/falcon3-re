import struct
import math

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

f16 = data[offsets[3]:offsets[4]]

sig_pos = f16.find(b'\xFF\xFF\x00\x40')
lod_table_pos = sig_pos + 4
vc, vo, to, w3, w4 = struct.unpack_from('<5H', f16, lod_table_pos)

verts = []
for vi in range(vc):
    x, y, z = struct.unpack_from('<hhh', f16, vo + vi * 6)
    # raw coords in OpenGL space (y/10, -z/10, -x/10)
    verts.append([round(y / 10.0, 2), round(-z / 10.0, 2), round(-x / 10.0, 2)])

# Collect all polygon offsets referenced in the pointer table
ptr = to
poly_offsets = set()

while ptr + 2 <= len(f16):
    node_off = struct.unpack_from('<H', f16, ptr)[0]
    ptr += 2
    if node_off == 0xFFFF:
        break
    if node_off >= len(f16):
        continue
    w0 = struct.unpack_from('<H', f16, node_off)[0]
    if w0 == 0xFFFF:
        # Group node: array of polygon pointers
        sub_ptr = node_off + 2
        while sub_ptr + 2 <= len(f16):
            target = struct.unpack_from('<H', f16, sub_ptr)[0]
            sub_ptr += 2
            if target == 0xFFFF or target == 0:
                break
            if target < len(f16):
                poly_offsets.add(target)
    else:
        # Direct polygon definition
        poly_offsets.add(node_off)

sorted_polys = sorted(list(poly_offsets))

faces = []
for p in sorted_polys:
    if p + 8 <= len(f16):
        norm, mode, col, cnt = struct.unpack_from('<4H', f16, p)
        if 3 <= cnt <= 20 and p + 8 + (cnt+1)*2 <= len(f16):
            v_words = struct.unpack_from(f'<{cnt+1}H', f16, p + 8)
            v_idxs = [w // 16 for w in v_words[:-1]]
            faces.append({'offset': hex(p), 'color': col, 'indices': v_idxs})

print(f"Total authentic faces: {len(faces)}")

def vec_sub(a, b):
    return [a[0]-b[0], a[1]-b[1], a[2]-b[2]]

def cross(a, b):
    return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]

def dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def mag(a):
    return math.sqrt(dot(a, a))

for fi, f in enumerate(faces):
    idxs = f['indices']
    f_verts = [verts[i] for i in idxs]
    n = len(idxs)
    max_dist = 0.0
    if n >= 4:
        p0, p1, p2 = f_verts[0], f_verts[1], f_verts[2]
        v1 = vec_sub(p1, p0)
        v2 = vec_sub(p2, p0)
        norm = cross(v1, v2)
        m = mag(norm)
        if m > 1e-4:
            un = [x/m for x in norm]
            for v in f_verts[3:]:
                d = abs(dot(vec_sub(v, p0), un))
                if d > max_dist:
                    max_dist = d
    warp_str = f"WARPED ({max_dist:.2f})" if max_dist > 1.5 else "OK"
    print(f"Face {fi:2d} (off={f['offset']}, {n}-gon, col={f['color']:3d}): {idxs} -> {warp_str}")
