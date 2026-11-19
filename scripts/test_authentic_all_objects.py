import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

stats = []

for i in range(num_objs):
    off = offsets[i]
    next_off = offsets[i+1] if i+1 < num_objs else len(data)
    obj_bytes = data[off:next_off]
    
    name = f"OBJ_{i:02d}"
    if len(obj_bytes) > 12:
        nchunk = obj_bytes[4:12]
        if all(32 <= b <= 126 or b == 0 for b in nchunk):
            s = nchunk.decode('ascii', errors='ignore').replace('\x00', '').strip()
            if s:
                name = s

    sig_pos = obj_bytes.find(b'\xFF\xFF\x00\x40')
    if sig_pos == -1:
        continue
        
    lod_table_pos = sig_pos + 4
    for lod_idx in range(4):
        if lod_table_pos + (lod_idx+1)*10 <= len(obj_bytes):
            vc, vo, to, w3, w4 = struct.unpack_from('<5H', obj_bytes, lod_table_pos + lod_idx*10)
            if 0 < vc < 3000 and 0 < vo < len(obj_bytes) and 0 < to < len(obj_bytes):
                # Traverse pointer table at 'to'
                ptr = to
                poly_offsets = set()
                while ptr + 2 <= len(obj_bytes):
                    node_off = struct.unpack_from('<H', obj_bytes, ptr)[0]
                    ptr += 2
                    if node_off == 0xFFFF:
                        break
                    if node_off >= len(obj_bytes):
                        continue
                    w0 = struct.unpack_from('<H', obj_bytes, node_off)[0]
                    if w0 == 0xFFFF:
                        # Group node: array of polygon pointers
                        sub_ptr = node_off + 2
                        while sub_ptr + 2 <= len(obj_bytes):
                            target = struct.unpack_from('<H', obj_bytes, sub_ptr)[0]
                            sub_ptr += 2
                            if target == 0xFFFF or target == 0:
                                break
                            if target < len(obj_bytes):
                                poly_offsets.add(target)
                    else:
                        poly_offsets.add(node_off)
                
                # Unpack polygons
                faces = []
                for p in sorted(list(poly_offsets)):
                    if p + 8 <= len(obj_bytes):
                        norm, mode, col, cnt = struct.unpack_from('<4H', obj_bytes, p)
                        if 3 <= cnt <= 20 and p + 8 + (cnt+1)*2 <= len(obj_bytes):
                            v_words = struct.unpack_from(f'<{cnt+1}H', obj_bytes, p + 8)
                            if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
                                ring = [w // 16 for w in v_words[:-1]]
                                if len(set(ring)) >= 3:
                                    faces.append((col, ring))
                
                stats.append((name, lod_idx, vc, len(faces)))

print(f"Total objects/LODs processed: {len(stats)}")
for s in stats[:20]:
    print(f"  {s[0]:10s} LOD {s[1]}: {s[2]:3d} verts, {s[3]:3d} faces")
