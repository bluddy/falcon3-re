import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

vc, vo, to = struct.unpack_from('<3H', obj, 0x40)
raw_verts = [struct.unpack_from('<hhh', obj, vo + i*6) for i in range(vc)]

# Check all faces from our script
octant_ptrs = [0x0232, 0x0288, 0x02de, 0x0330, 0x0382, 0x03ce, 0x041a, 0x0466]
all_node_ptrs = set()

for oct_ptr in octant_ptrs:
    p = oct_ptr
    if struct.unpack_from('<H', obj, p)[0] == 0xFFFF:
        p += 2
    while p + 2 <= len(obj):
        node = struct.unpack_from('<H', obj, p)[0]
        p += 2
        if node == 0xFFFF or node == 0:
            break
        if 0x400 <= node < len(obj):
            all_node_ptrs.add(node)

def parse_object_node(data, p, vc):
    if p + 8 > len(data):
        return []
    norm, mode, col, cnt = struct.unpack_from('<4H', data, p)
    faces = []
    if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= len(data):
        v_words = struct.unpack_from(f'<{cnt+1}H', data, p + 8)
        if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
            ring = [w // 16 for w in v_words[:-1]]
            faces.append({'color': col & 0xFF, 'indices': ring, 'offset': p, 'norm': norm, 'mode': mode})
            next_p = p + 8 + (cnt + 1) * 2
            while next_p + 8 <= len(data):
                n2, m2, c2, cnt2 = struct.unpack_from('<4H', data, next_p)
                if 3 <= cnt2 <= 16 and next_p + 8 + (cnt2 + 1) * 2 <= len(data):
                    v_words2 = struct.unpack_from(f'<{cnt2+1}H', data, next_p + 8)
                    if all(w % 16 == 0 and (w // 16) < vc for w in v_words2):
                        ring2 = [w // 16 for w in v_words2[:-1]]
                        faces.append({'color': c2 & 0xFF, 'indices': ring2, 'offset': next_p, 'norm': n2, 'mode': m2})
                        next_p += 8 + (cnt2 + 1) * 2
                        continue
                break
    return faces

all_faces = []
unique_rings = set()
for node in sorted(all_node_ptrs):
    for f in parse_object_node(obj, node, vc):
        k = tuple(sorted(f['indices']))
        if k not in unique_rings:
            unique_rings.add(k)
            all_faces.append(f)

print(f"Total faces: {len(all_faces)}")
for i, f in enumerate(all_faces):
    # Print vertices of this face
    pts = [raw_verts[idx] for idx in f['indices']]
    print(f"Face {i:2d} (col={f['color']:3d}, node=0x{f['offset']:04x}): indices={f['indices']}")
    for idx, pt in zip(f['indices'], pts):
        print(f"    v{idx:02d}: {pt}")
