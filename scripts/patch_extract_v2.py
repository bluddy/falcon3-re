with open('scripts/extract_all_3d_assets.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace find_lod_table and the entire decode_objects_archive body
start_marker = "def find_lod_table(obj):"
end_marker = "def decode_mapobj_archive(filepath='game/MAPOBJ'):"

new_code = '''def find_lod_table(obj):
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

def decode_objects_archive(filepath='game/OBJECTS'):
    with open(filepath, 'rb') as f:
        data = f.read()

    first_off = struct.unpack_from('<I', data, 0)[0]
    num_objs = first_off // 4
    offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

    objects = []
    
    for i in range(num_objs):
        off = offsets[i]
        next_off = offsets[i+1] if i+1 < num_objs else len(data)
        obj = data[off:next_off]
        
        name = ''
        if len(obj) > 12:
            nchunk = obj[4:12]
            if all(32 <= b <= 126 or b == 0 for b in nchunk):
                name = nchunk.decode('ascii', errors='ignore').replace('\\x00', '').strip()
        if not name:
            name = f"OBJ_{i:02d}"

        byte2 = struct.unpack_from('<H', obj, 2)[0] if len(obj) >= 4 else 0
        
        all_verts = []
        all_faces = []
        lods = []
        
        # Authentic Aviation NED -> OpenGL transform:
        # X_gl = Y_ned / 10.0 (Right/Starboard)
        # Y_gl = -Z_ned / 10.0 (Up/Dorsal fin)
        # Z_gl = X_ned / 10.0 (Forward/Nose toward camera like REPORT.DAT)
        is_multipart_tank = (byte2 == 0x010a and i != 38)
        
        if is_multipart_tank:
            parts = []
            p = 0x60
            while p + 10 <= len(obj):
                flags, vc, w2, node_ptr, w4 = struct.unpack_from('<5H', obj, p)
                if vc == 0 or node_ptr == 0 or node_ptr >= len(obj):
                    break
                vo = node_ptr - vc * 6
                if vo < 0:
                    break
                parts.append((vc, vo, node_ptr))
                p += 10
            
            v_base = 0
            for part_idx, (vc, vo, node_ptr) in enumerate(parts):
                next_part_vo = parts[part_idx+1][1] if part_idx + 1 < len(parts) else len(obj)
                part_verts = [struct.unpack_from('<hhh', obj, vo + j*6) for j in range(vc)]
                gl_verts = [[round(v[1]/10.0, 2), round(-v[2]/10.0, 2), round(v[0]/10.0, 2)] for v in part_verts]
                all_verts.extend(gl_verts)
                
                unique = set()
                for p_node in range(node_ptr, next_part_vo - 8, 2):
                    norm, mode, col, cnt = struct.unpack_from('<4H', obj, p_node)
                    if 3 <= cnt <= 16 and p_node + 8 + (cnt + 1) * 2 <= next_part_vo:
                        v_words = struct.unpack_from(f'<{cnt+1}H', obj, p_node + 8)
                        if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                            ring = [w // 16 + v_base for w in v_words[:-1]]
                            k = tuple(sorted(ring))
                            if k not in unique:
                                unique.add(k)
                                all_faces.append({'color': col & 0xFF, 'indices': ring})
                v_base += vc
            
            edges = set()
            for f_item in all_faces:
                ring = f_item['indices']
                for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                    edges.add(tuple(sorted([v1, v2])))
            
            lods.append({
                'lod': 0,
                'vertex_count': len(all_verts),
                'face_count': len(all_faces),
                'edge_count': len(edges),
                'vertices': all_verts,
                'faces': all_faces,
                'edges': [list(e) for e in sorted(list(edges))]
            })
        else:
            table_p, lod_headers = find_lod_table(obj)
            if lod_headers:
                for idx, (lod_idx, vc, vo, to) in enumerate(lod_headers):
                    raw_verts = [struct.unpack_from('<hhh', obj, vo + j*6) for j in range(vc)]
                    verts = [[round(v[1] / 10.0, 2), round(-v[2] / 10.0, 2), round(v[0] / 10.0, 2)] for v in raw_verts]
                    
                    next_to = lod_headers[idx+1][3] if idx + 1 < len(lod_headers) else len(obj)
                    if next_to <= to or next_to > len(obj):
                        next_to = len(obj)
                    
                    faces = []
                    unique = set()
                    scan_start = max(to, vo + vc * 6)
                    # 1. Strictly bounded scan within LOD range
                    for p in range(scan_start, next_to - 8, 2):
                        norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
                        if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= next_to:
                            v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
                            if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
                                if v_words[0] == v_words[-1]:
                                    ring = [w // 16 for w in v_words[:-1]]
                                    k = tuple(sorted(ring))
                                    if k not in unique:
                                        unique.add(k)
                                        faces.append({'color': col & 0xFF, 'indices': ring})
                    
                    # 2. If strictly bounded gave 0 faces (tree pointers precede shared node pool), scan to end
                    if not faces:
                        for p in range(scan_start, len(obj) - 8, 2):
                            norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
                            if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= len(obj):
                                v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
                                if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
                                    if v_words[0] == v_words[-1]:
                                        ring = [w // 16 for w in v_words[:-1]]
                                        k = tuple(sorted(ring))
                                        if k not in unique:
                                            unique.add(k)
                                            faces.append({'color': col & 0xFF, 'indices': ring})
                    
                    edges = set()
                    for f_item in faces:
                        ring = f_item['indices']
                        for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                            edges.add(tuple(sorted([v1, v2])))
                    
                    lod_dict = {
                        'lod': lod_idx,
                        'vertex_count': len(verts),
                        'face_count': len(faces),
                        'edge_count': len(edges),
                        'vertices': verts,
                        'faces': faces,
                        'edges': [list(e) for e in sorted(list(edges))]
                    }
                    lods.append(lod_dict)
                    
                    if lod_idx == 0:
                        all_verts = verts
                        all_faces = faces
        
        edges = set()
        for f_item in all_faces:
            ring = f_item['indices']
            for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                edges.add(tuple(sorted([v1, v2])))
        
        cat = 'Generic'
        name_u = name.upper()
        if any(w in name_u for w in ['TANK', 'T72', 'T80', 'M1', 'BMP', 'BTR', 'ZSU', 'SHILKA', 'TRUCK', 'JEEP', 'M60', 'M113', 'AMX', 'BDRM', 'WALID']):
            cat = 'Ground Vehicle'
        elif any(w in name_u for w in ['SAM', 'SCUD', 'HAWK', 'PATRIOT', 'SA2', 'SA6', 'SA8', 'SA13', 'SHAHINE', 'BGM']):
            cat = 'Air Defense'
        elif any(w in name_u for w in ['BOAT', 'SHIP', 'FRIGATE', 'PATROL', 'LCI', 'LST', 'LEBED', 'NIMITZ']):
            cat = 'Naval Unit'
        elif any(w in name_u for w in ['MIG', 'SU', 'F16', 'F-16', 'F15', 'F-15', 'F4', 'F-4', 'MIRAGE', 'MIR', 'BEAR', 'IL76', 'A10', 'A4', 'FA18', 'F14', 'F111', 'F117', 'FSX', 'J7', 'Q5', 'JAGUAR', 'B52', 'C130', 'E3', 'TU22', 'AN12', 'KFIR', 'TORNADO', 'AH64', 'UH60', 'SA342', 'MI24', 'UMF', 'F1', 'F5']):
            cat = 'Aircraft'
        elif 'TOWER' in name_u or 'OBJ_4' in name_u or 'OBJ_5' in name_u:
            cat = 'Structure'

        objects.append({
            'id': i,
            'name': name,
            'category': cat,
            'source': 'OBJECTS',
            'vertex_count': len(all_verts),
            'face_count': len(all_faces),
            'edge_count': len(edges),
            'vertices': all_verts,
            'faces': all_faces,
            'edges': [list(e) for e in sorted(list(edges))],
            'lods': lods if lods else [{
                'lod': 0,
                'vertex_count': len(all_verts),
                'face_count': len(all_faces),
                'edge_count': len(edges),
                'vertices': all_verts,
                'faces': all_faces,
                'edges': [list(e) for e in sorted(list(edges))]
            }]
        })

    return objects

'''

p1 = text.find(start_marker)
p2 = text.find(end_marker)

if p1 != -1 and p2 != -1:
    new_text = text[:p1] + new_code + text[p2:]
    with open('scripts/extract_all_3d_assets.py.tmp', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("SUCCESS: Wrote scripts/extract_all_3d_assets.py.tmp")
else:
    print(f"ERROR: Markers not found: p1={p1}, p2={p2}")
