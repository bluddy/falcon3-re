import struct

# REPORT J7
rep_data = open('game/REPORT.DAT', 'rb').read()
sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]
s_off = sec_offsets[0]
rel = struct.unpack_from('<I', rep_data, s_off + 2 + 21 * 4)[0]
abs_off = s_off + rel
sz = struct.unpack_from('<H', rep_data, abs_off)[0]
j7_rep = rep_data[abs_off+2 : abs_off+2+sz]
rec_off = struct.unpack_from('<H', j7_rep, 4)[0]
vc_r, vo_r, to_r = struct.unpack_from('<3H', j7_rep, rec_off + 50)

# OBJECTS J7
obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
j7_obj = obj_data[offsets[57] : offsets[58]]
vc_o, vo_o, to_o = struct.unpack_from('<3H', j7_obj, 0x0040)

# Extract REPORT faces
# to_r is at 0x1693
# Let's see how REPORT.DAT extracts faces using resolve_octant_or_node
def parse_rep_node(data, node_off):
    flags = struct.unpack_from('<H', data, node_off)[0]
    col = data[node_off + 2]
    cnt = struct.unpack_from('<H', data, node_off + 4)[0]
    faces = []
    if 3 <= cnt <= 16 and node_off + 6 + (cnt+1)*2 <= len(data):
        v_words = struct.unpack_from(f'<{cnt+1}H', data, node_off + 6)
        if all(w % 16 == 0 and w // 16 < vc_r for w in v_words) and v_words[0] == v_words[-1]:
            faces.append({'col': col, 'indices': [w // 16 for w in v_words[:-1]]})
    return faces

# Scan REPORT octants
rep_faces = []
unique_r = set()
for octant in range(8):
    ptr = struct.unpack_from('<H', j7_rep, to_r + octant * 2)[0]
    if ptr == 0xffff or ptr >= len(j7_rep):
        break
    p = ptr
    while p + 2 <= len(j7_rep):
        node = struct.unpack_from('<H', j7_rep, p)[0]
        p += 2
        if node == 0xffff:
            break
        for f in parse_rep_node(j7_rep, node):
            k = tuple(sorted(f['indices']))
            if k not in unique_r:
                unique_r.add(k)
                rep_faces.append(f)

print(f"REPORT J7 faces count: {len(rep_faces)}")

# Extract OBJECTS J7 faces
# to_o = 0x0210, next_to = 0x081e (LOD 1 to)
next_to_o = struct.unpack_from('<H', j7_obj, 0x004a + 4)[0]
print(f"OBJECTS J7 to: 0x{to_o:04x}, next_to: 0x{next_to_o:04x}")

obj_faces = []
unique_o = set()
for p in range(to_o, next_to_o - 8, 2):
    norm, mode, col, cnt = struct.unpack_from('<4H', j7_obj, p)
    if 3 <= cnt <= 16 and p + 8 + (cnt+1)*2 <= next_to_o:
        v_words = struct.unpack_from(f'<{cnt+1}H', j7_obj, p + 8)
        if all(w % 16 == 0 and w // 16 < vc_o for w in v_words) and v_words[0] == v_words[-1]:
            indices = [w // 16 for w in v_words[:-1]]
            k = tuple(sorted(indices))
            if k not in unique_o:
                unique_o.add(k)
                obj_faces.append({'col': col, 'indices': indices})

print(f"OBJECTS J7 faces count: {len(obj_faces)}")

print("\n--- Comparing first 20 faces ---")
print("Idx | REPORT.DAT face                   | OBJECTS face")
print("----+-----------------------------------+-----------------------------------")
for i in range(min(len(rep_faces), len(obj_faces), 20)):
    rf = rep_faces[i]
    of = obj_faces[i]
    print(f" {i:02d} | col={rf['col']:3d}, idx={rf['indices']} | col={of['col']:3d}, idx={of['indices']}")
