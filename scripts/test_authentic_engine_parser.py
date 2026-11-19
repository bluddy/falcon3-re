import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

f16 = data[offsets[3]:offsets[4]]

# Chunk header:
# 0..3: ?
# 4..11: name 'F16     \x00'
name = f16[4:12].decode('ascii', errors='ignore').strip('\x00 ')

sig_pos = f16.find(b'\xFF\xFF\x00\x40')
lod_table_pos = sig_pos + 4
vc, vo, to, w3, w4 = struct.unpack_from('<5H', f16, lod_table_pos)

print(f"Object: {name}")
print(f"LOD 0: vc={vc}, vo={hex(vo)}, to={hex(to)}")

# Read vertices
verts = []
for vi in range(vc):
    x, y, z = struct.unpack_from('<hhh', f16, vo + vi * 6)
    verts.append((x, y, z))

print(f"Read {len(verts)} vertices")

# Now follow the REAL engine parser:
ptr = to
parsed_nodes = []
all_polys = []

while ptr + 2 <= len(f16):
    node_off = struct.unpack_from('<H', f16, ptr)[0]
    ptr += 2
    if node_off == 0xFFFF:
        print(f"End of 'to' table at {hex(ptr-2)}")
        break
    if node_off >= len(f16):
        continue
        
    # Unpack node header at node_off:
    flags = struct.unpack_from('<H', f16, node_off)[0]
    color = f16[node_off + 2]
    flags2 = f16[node_off + 3]
    has_sublist = bool(flags & 0x1000)
    dispatch_mode = flags & 2
    
    if has_sublist:
        # sublist of relative pointers
        sub_ptr = node_off + 4
        sub_polys = []
        while sub_ptr + 2 <= len(f16):
            rel_off = struct.unpack_from('<h', f16, sub_ptr)[0]
            if rel_off == -1 or rel_off == 0xFFFF:
                break
            # In asm: di = [si]; add di, 2; shl di, 1; add di, si
            target_poly_off = sub_ptr + (rel_off + 1) * 2
            sub_polys.append(target_poly_off)
            sub_ptr += 2
        parsed_nodes.append(('GROUP', hex(node_off), flags, color, sub_polys))
    else:
        # Direct polygon at node_off + 4
        poly_off = node_off + 4
        parsed_nodes.append(('POLY', hex(node_off), flags, color, [poly_off]))

print(f"Parsed {len(parsed_nodes)} nodes from pointer table:")
for kind, off, fl, col, polys in parsed_nodes:
    print(f"  {kind} at {off}: flags=0x{fl:04x}, color={col}, targets={[hex(p) for p in polys]}")
    for p in polys:
        if p + 2 <= len(f16):
            cnt = struct.unpack_from('<H', f16, p)[0]
            if 3 <= cnt <= 20 and p + 2 + cnt * 2 <= len(f16):
                v_words = struct.unpack_from(f'<{cnt}H', f16, p + 2)
                v_idxs = [w // 16 for w in v_words]
                all_polys.append({'node_off': off, 'poly_off': hex(p), 'color': col, 'indices': v_idxs})
                print(f"      Poly at {hex(p)}: {cnt} verts -> {v_idxs}")

print(f"\nTotal polygons discovered via authentic engine pointers: {len(all_polys)}")
