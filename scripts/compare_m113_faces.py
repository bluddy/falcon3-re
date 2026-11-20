import struct

# REPORT.DAT M113
rep_data = open('game/REPORT.DAT', 'rb').read()
sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]
s_off = sec_offsets[2]
rel = struct.unpack_from('<I', rep_data, s_off + 2 + 4 * 4)[0]
m113_rep = rep_data[s_off + rel + 2 :]

# OBJECTS M113
obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
m113_obj = obj_data[offsets[36] : offsets[37]]

print("=== REPORT.DAT Part 0 Faces ===")
# to = 0x1805
p_node = 0x1805
rep_faces = []
while p_node + 2 <= len(m113_rep):
    node_off = struct.unpack_from('<H', m113_rep, p_node)[0]
    p_node += 2
    if node_off == 0xffff:
        break
    flags = struct.unpack_from('<H', m113_rep, node_off)[0]
    col = m113_rep[node_off + 2]
    cnt = struct.unpack_from('<H', m113_rep, node_off + 4)[0]
    v_words = struct.unpack_from(f'<{cnt+1}H', m113_rep, node_off + 6)
    indices = [w // 16 for w in v_words[:-1]]
    rep_faces.append((col, indices))
    print(f"Node 0x{node_off:04x}: color={col}, count={cnt}, indices={indices}")

print(f"Total REPORT.DAT faces: {len(rep_faces)}")

print("\n=== OBJECTS Part 0 Nodes / Faces ===")
# In OBJECTS: to = 0x00e4. Where does Part 0 nodes end? Part 1 to is 0x019e, or part 1 vo is 0x048a?
# Let's inspect bytes starting from 0x00e4
for p in range(0x00e4, 0x019e, 2):
    w0 = struct.unpack_from('<H', m113_obj, p)[0]
    # Check if this looks like a node
    if p + 8 <= len(m113_obj):
        norm, mode, col, cnt = struct.unpack_from('<4H', m113_obj, p)
        if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= len(m113_obj):
            v_words = struct.unpack_from(f'<{cnt+1}H', m113_obj, p + 8)
            if all(w % 16 == 0 and (w // 16) < 14 for w in v_words) and v_words[0] == v_words[-1]:
                indices = [w // 16 for w in v_words[:-1]]
                print(f"At 0x{p:04x}: norm=0x{norm:04x}, mode=0x{mode:04x}, col={col}, cnt={cnt}, indices={indices}")
