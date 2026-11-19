import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

f16 = data[offsets[3]:offsets[4]]

sig_pos = f16.find(b'\xFF\xFF\x00\x40')
lod_table_pos = sig_pos + 4
vc, vo, to, w3, w4 = struct.unpack_from('<5H', f16, lod_table_pos)

ptr = to
nodes = []
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
print(f"Found {len(sorted_polys)} unique polygon offsets in F-16 Chunk 3!\n")

clean_faces = []
for p in sorted_polys:
    if p + 8 <= len(f16):
        norm, mode, col, cnt = struct.unpack_from('<4H', f16, p)
        if 3 <= cnt <= 20 and p + 8 + (cnt+1)*2 <= len(f16):
            v_words = struct.unpack_from(f'<{cnt+1}H', f16, p + 8)
            v_idxs = [w // 16 for w in v_words[:-1]]
            closed = (v_words[0] == v_words[-1])
            clean_faces.append({
                'offset': hex(p),
                'color': col,
                'count': cnt,
                'indices': v_idxs,
                'closed': closed
            })
            print(f"Poly at {hex(p)}: col={col:3d}, cnt={cnt:2d}, closed={closed} -> {v_idxs}")

print(f"\nTotal clean, authentic polygons: {len(clean_faces)}")
