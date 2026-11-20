import re

with open('scripts/extract_all_3d_assets.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Helper function find_lod_table before decode_objects_archive
helper = '''def find_lod_table(obj):
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

def decode_objects_archive(filepath=\'game/OBJECTS\'):'''

text = text.replace("def decode_objects_archive(filepath='game/OBJECTS'):", helper)

target_body = """        # 1. Check if multi-part tank (has part table at 0x60 with Chassis, Hull, Turret)
        # Ground vehicles with 0x010a except WALID (which has standard LOD header at 0x34)
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
                gl_verts = [[round(v[1]/10.0, 2), round(v[2]/10.0, 2), round(-v[0]/10.0, 2)] for v in part_verts]
                all_verts.extend(gl_verts)
                
                unique = set()
                for p_node in range(node_ptr, next_part_vo - 8, 2):
                    norm, mode, col, cnt = struct.unpack_from('<4H', obj, p_node)
                    if 3 <= cnt <= 16 and p_node + 8 + (cnt + 1) * 2 <= len(obj):
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
            lod_table_pos = -1
            if i == 1: # TORNADO
                lod_table_pos = 0x148
            elif i == 67: # NIMITZ
                lod_table_pos = 0x0024
            elif i == 69: # MEAT
                lod_table_pos = 0x0014
            elif i == 70: # STROBE
                lod_table_pos = 0x001c
            else:
                sig = obj.find(b'\\xff\\xff\\x00\\x40')
                if sig != -1 and sig + 10 <= len(obj):
                    lod_table_pos = sig + 4
            
            if lod_table_pos != -1:
                lod_headers = []
                for lod_idx in range(4):
                    if lod_table_pos + (lod_idx + 1) * 10 <= len(obj):
                        vc, vo, to, w3, w4 = struct.unpack_from('<5H', obj, lod_table_pos + lod_idx * 10)
                        if 0 < vc < 3000 and 0 <= vo < len(obj) and vo + vc * 6 <= len(obj):
                            lod_headers.append((lod_idx, vc, vo, to))
                
                for lod_idx, vc, vo, to in lod_headers:
                    raw_verts = [struct.unpack_from('<hhh', obj, vo + j*6) for j in range(vc)]
                    verts = [[round(v[1] / 10.0, 2), round(v[2] / 10.0, 2), round(-v[0] / 10.0, 2)] for v in raw_verts]
                    
                    faces = []
                    unique = set()
                    scan_start = max(to, vo + vc * 6)
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
                        all_faces = faces"""

replacement_body = """        # Authentic NED -> OpenGL transform:
        # X_gl = Y_ned / 10.0 (Right/Starboard)
        # Y_gl = -Z_ned / 10.0 (Up/Dorsal)
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
                    for p in range(scan_start, next_to - 8, 2):
                        norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
                        if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= next_to:
                            v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
                            if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
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
                        all_faces = faces"""

if target_body in text:
    text = text.replace(target_body, replacement_body)
    with open('scripts/extract_all_3d_assets.py.tmp', 'w', encoding='utf-8') as f:
        f.write(text)
    print("SUCCESS: Prepared updated extract_all_3d_assets.py.tmp")
else:
    print("ERROR: Target body not found in text")
