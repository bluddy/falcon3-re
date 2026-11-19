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

# 1. Read vertices
verts = []
for vi in range(vc):
    x, y, z = struct.unpack_from('<hhh', f16, vo + vi * 6)
    verts.append((x, y, z))

print(f"Loaded {len(verts)} vertices")

# 2. Parse exactly according to FALCONCD.EXE:
ptr = to
nodes = []
polygons = []

while ptr + 2 <= len(f16):
    node_off = struct.unpack_from('<H', f16, ptr)[0]
    ptr += 2
    if node_off == 0xFFFF:
        break
    if node_off >= len(f16):
        continue
        
    flags = struct.unpack_from('<H', f16, node_off)[0]
    color = f16[node_off + 2]
    flags2 = f16[node_off + 3]
    has_sublist = bool(flags & 0x1000)
    dispatch_mode = flags & 2
    
    if not has_sublist:
        # Single polygon at node_off + 4
        # Format: word count, (count+1) vertex words (each index*16)
        p = node_off + 4
        cnt = struct.unpack_from('<H', f16, p)[0]
        v_words = struct.unpack_from(f'<{cnt+1}H', f16, p + 2)
        v_indices = [w // 16 for w in v_words[:-1]]
        polygons.append({
            'source': 'DIRECT',
            'node_off': hex(node_off),
            'flags': hex(flags),
            'color': color,
            'count': cnt,
            'indices': v_indices
        })
    else:
        # Sublist of polygons starting at node_off + 4
        si = node_off + 4
        while si + 2 <= len(f16):
            cnt = struct.unpack_from('<H', f16, si)[0]
            if cnt == 0xFFFF:
                break
            # Poly has cnt vertices
            # Total size is (cnt + 2) * 2 bytes
            next_si = si + (cnt + 2) * 2
            v_words = struct.unpack_from(f'<{cnt+1}H', f16, si + 2)
            v_indices = [w // 16 for w in v_words[:-1]]
            polygons.append({
                'source': 'SUBLIST',
                'node_off': hex(node_off),
                'flags': hex(flags),
                'color': color,
                'count': cnt,
                'indices': v_indices
            })
            si = next_si

print(f"Total authentic polygons parsed: {len(polygons)}\n")
for idx, poly in enumerate(polygons):
    print(f"Poly {idx:2d}: {poly['source']} at {poly['node_off']}, col={poly['color']:3d}, cnt={poly['count']} -> {poly['indices']}")
