import struct
import json
from pathlib import Path

def decode_all_objects(filepath='game/OBJECTS'):
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
                name = nchunk.decode('ascii', errors='ignore').replace('\x00', '').strip()
        if not name:
            name = f"OBJ_{i:02d}"

        byte2 = struct.unpack_from('<H', obj, 2)[0] if len(obj) >= 4 else 0
        
        all_verts = []
        all_faces = []
        lods = []
        
        # Check if multi-part tank / ground vehicle (14-byte part records)
        sig_tank = obj.find(b'\x08\x04\xf0') # common part table signature or check byte2 == 0x010a
        is_multipart_tank = (byte2 == 0x010a)
        
        if is_multipart_tank:
            # Multi-part tank parsing
            v_base = 0
            part_records = []
            for p in range(0x40, min(0x120, len(obj) - 14), 14):
                w_row = struct.unpack_from('<7H', obj, p)
                part_rec_ptr = w_row[5]
                if part_rec_ptr != 0 and part_rec_ptr + 10 <= len(obj):
                    vc, vo, to, w3, w4 = struct.unpack_from('<5H', obj, part_rec_ptr)
                    if 2 <= vc <= 100 and vo < len(obj) and to < len(obj):
                        part_records.append((vc, vo, to))
            
            for vc, vo, to in part_records:
                part_verts = [struct.unpack_from('<hhh', obj, vo + j*6) for j in range(vc)]
                # Tanks: X=length, Y=width, Z=height
                all_verts.extend([[round(v[1] / 10.0, 2), round(v[2] / 10.0, 2), round(-v[0] / 10.0, 2)] for v in part_verts])
                
                # Scan nodes for this part
                for p_node in range(to, min(len(obj) - 8, to + 400), 2):
                    norm, mode, col, cnt = struct.unpack_from('<4H', obj, p_node)
                    if 3 <= cnt <= 16 and p_node + 8 + (cnt + 1) * 2 <= len(obj):
                        v_words = struct.unpack_from(f'<{cnt+1}H', obj, p_node + 8)
                        if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
                            if v_words[0] == v_words[-1]:
                                ring = [w // 16 + v_base for w in v_words[:-1]]
                                all_faces.append({'color': col & 0xFF, 'indices': ring})
                v_base += vc
        else:
            # Standard single-piece or multi-LOD model
            sig = obj.find(b'\xff\xff\x00\x40')
            if sig != -1 and sig + 10 <= len(obj):
                # Read LODs
                lod_table_pos = sig + 4
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
                        all_faces = faces
        
        edges = set()
        for f_item in all_faces:
            ring = f_item['indices']
            for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                edges.add(tuple(sorted([v1, v2])))
        
        cat = 'Generic'
        if any(w in name.upper() for w in ['MIG', 'SU', 'F16', 'F-16', 'F15', 'F-15', 'F4', 'F-4', 'MIRAGE', 'BEAR', 'IL76', 'A10', 'A4', 'FA18', 'F14', 'F111', 'F117', 'FSX', 'J7', 'Q5', 'JAGUAR', 'B52', 'C130', 'E3', 'TU22', 'AN12', 'KFIR', 'TORNADO', 'AH64', 'UH60', 'SA342', 'MI24', 'UMF']):
            cat = 'Aircraft'
        elif any(w in name.upper() for w in ['TANK', 'T72', 'T80', 'M1', 'BMP', 'BTR', 'ZSU', 'SHILKA', 'TRUCK', 'JEEP', 'M60', 'M113', 'AMX', 'BDRM', 'WALID']):
            cat = 'Ground Vehicle'
        elif any(w in name.upper() for w in ['BOAT', 'SHIP', 'FRIGATE', 'PATROL', 'LCI', 'LST', 'LEBED', 'NIMITZ']):
            cat = 'Naval Unit'
        elif any(w in name.upper() for w in ['SAM', 'SCUD', 'HAWK', 'PATRIOT', 'SA2', 'SA6', 'SA8', 'SA13', 'SHAHINE', 'BGM']):
            cat = 'Air Defense'

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

objs = decode_all_objects()
print(f"Decoded {len(objs)} objects from game/OBJECTS")
with_faces = [o for o in objs if o['face_count'] > 0]
print(f"Objects with valid 3D geometry: {len(with_faces)} / {len(objs)}")
for o in with_faces[:20]:
    print(f"  [{o['id']:02d}] {o['name']:12s} ({o['category']:14s}): {o['vertex_count']:3d} verts, {o['face_count']:2d} faces, {len(o['lods'])} LODs")
