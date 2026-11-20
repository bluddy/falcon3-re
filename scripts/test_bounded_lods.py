import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

print("Index | Name         | LODs | LOD 0 (v, f) | LOD 1 (v, f) | LOD 2 (v, f) | LOD 3 (v, f)")
print("-" * 75)

for i in range(num_objs):
    off = offsets[i]
    next_off = offsets[i+1] if i+1 < num_objs else len(data)
    obj = data[off:next_off]
    name = obj[4:12].decode('ascii', errors='ignore').strip()
    if not name: name = f"OBJ_{i:02d}"
    byte2 = struct.unpack_from('<H', obj, 2)[0] if len(obj) >= 4 else 0
    
    is_multipart_tank = (byte2 == 0x010a and i != 38)
    
    if is_multipart_tank:
        # Multi-part tank
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
                if 3 <= cnt <= 16 and p_node + 8 + (cnt + 1) * 2 <= len(obj):
                    v_words = struct.unpack_from(f'<{cnt+1}H', obj, p_node + 8)
                    if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                        ring = [w // 16 for w in v_words[:-1]]
                        k = tuple(sorted(ring))
                        if k not in unique:
                            unique.add(k)
                            total_f += 1
        print(f" {i:2d}   | {name:12s} |   1  | ({total_v:3d}, {total_f:2d})  |              |              |")
    else:
        # Find LOD table
        lod_table_pos = -1
        if i == 1: lod_table_pos = 0x148
        elif i == 67: lod_table_pos = 0x0024
        elif i == 69: lod_table_pos = 0x0014
        elif i == 70: lod_table_pos = 0x001c
        else:
            sig = obj.find(b'\xff\xff\x00\x40')
            if sig != -1 and sig + 10 <= len(obj):
                lod_table_pos = sig + 4
        
        if lod_table_pos == -1:
            print(f" {i:2d}   | {name:12s} |   0  | NO TABLE     |")
            continue
        
        lod_headers = []
        for lod_idx in range(4):
            if lod_table_pos + (lod_idx + 1) * 10 <= len(obj):
                vc, vo, to, w3, w4 = struct.unpack_from('<5H', obj, lod_table_pos + lod_idx * 10)
                if 0 < vc < 3000 and 0 <= vo < len(obj) and vo + vc * 6 <= len(obj):
                    lod_headers.append((lod_idx, vc, vo, to))
        
        lod_results = []
        for idx, (lod_idx, vc, vo, to) in enumerate(lod_headers):
            # next_to is next LOD's 'to', or end of obj for the last one
            next_to = lod_headers[idx+1][3] if idx+1 < len(lod_headers) else len(obj)
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
            lod_results.append((vc, len(unique)))
        
        res_str = " | ".join(f"({v:3d}, {f:2d})" for v, f in lod_results)
        print(f" {i:2d}   | {name:12s} |   {len(lod_results)}  | {res_str}")
