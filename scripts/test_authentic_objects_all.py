import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

def find_lod_table(obj):
    best_p = -1
    best_lods = []
    for p in range(0x14, min(0x200, len(obj) - 10), 2):
        lods = []
        for lod_idx in range(4):
            if p + (lod_idx + 1) * 10 <= len(obj):
                vc, vo, to, w3, w4 = struct.unpack_from('<5H', obj, p + lod_idx * 10)
                if 2 <= vc <= 250 and 0x20 <= vo < len(obj) and vo + vc * 6 <= len(obj) and to < len(obj) and w3 == 0 and w4 == 0:
                    lods.append((lod_idx, vc, vo, to))
                else:
                    break
        if len(lods) > len(best_lods):
            best_lods = lods
            best_p = p
    return best_p, best_lods

for i in range(num_objs):
    off = offsets[i]
    next_off = offsets[i+1] if i+1 < num_objs else len(data)
    obj = data[off:next_off]
    name = obj[4:12].decode('ascii', errors='ignore').strip()
    if not name: name = f"OBJ_{i:02d}"
    byte2 = struct.unpack_from('<H', obj, 2)[0] if len(obj) >= 4 else 0
    
    is_multipart_tank = (byte2 == 0x010a and i != 38)
    
    if is_multipart_tank:
        parts = []
        p = 0x60
        while p + 10 <= len(obj):
            flags, vc, w2, node_ptr, w4 = struct.unpack_from('<5H', obj, p)
            if vc == 0 or node_ptr == 0 or node_ptr >= len(obj): break
            vo = node_ptr - vc * 6
            if vo < 0: break
            parts.append((vc, vo, node_ptr))
            p += 10
        total_v = sum(p[0] for p in parts)
        total_f = 0
        for part_idx, (vc, vo, node_ptr) in enumerate(parts):
            next_part_vo = parts[part_idx+1][1] if part_idx + 1 < len(parts) else len(obj)
            unique = set()
            for p_node in range(node_ptr, next_part_vo - 8, 2):
                norm, mode, col, cnt = struct.unpack_from('<4H', obj, p_node)
                if 3 <= cnt <= 16 and p_node + 8 + (cnt + 1) * 2 <= next_part_vo:
                    v_words = struct.unpack_from(f'<{cnt+1}H', obj, p_node + 8)
                    if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                        ring = [w // 16 for w in v_words[:-1]]
                        k = tuple(sorted(ring))
                        if k not in unique:
                            unique.add(k)
                            total_f += 1
        print(f"[{i:02d}] {name:12s}: Multi-Part Tank -> {total_v:2d}v, {total_f:2d}f")
    else:
        table_p, lod_headers = find_lod_table(obj)
        if not lod_headers:
            print(f"[{i:02d}] {name:12s}: NO LOD HEADERS")
            continue
        
        lod_stats = []
        for idx, (lod_idx, vc, vo, to) in enumerate(lod_headers):
            next_to = lod_headers[idx+1][3] if idx + 1 < len(lod_headers) else len(obj)
            if next_to <= to or next_to > len(obj):
                next_to = len(obj)
            
            unique = set()
            for p in range(to, next_to - 8, 2):
                norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
                if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= next_to:
                    v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
                    if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                        ring = [w // 16 for w in v_words[:-1]]
                        k = tuple(sorted(ring))
                        if k not in unique:
                            unique.add(k)
            lod_stats.append((vc, len(unique)))
        
        l0_v, l0_f = lod_stats[0]
        other_lods = ", ".join(f"L{idx}:({v}v,{f}f)" for idx, (v, f) in enumerate(lod_stats[1:], 1))
        print(f"[{i:02d}] {name:12s}: LOD 0: {l0_v:3d}v, {l0_f:2d}f | {len(lod_stats)} LODs [{other_lods}]")
