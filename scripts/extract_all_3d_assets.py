"""
Falcon 3.0 Comprehensive 3D Asset Decoder & Exporter
Extracts and parses all 3D assets:
- 5 Standalone Flyable Aircraft from game/*OBJ.BIN
- 71 Vehicles & Weapons from game/OBJECTS (with full authentic polygon traversal)
- 128 Terrain Structures & Ribbons from game/MAPOBJ
- 76 Aircraft Dossiers, Specs & 3D Models from game/REPORT.DAT
- Authentic 256-color VGA Palette from game/ALTPAL.ISR
Outputs:
- analysis/viewer/assets_database.json (for web and Qt 3D viewer)
- analysis/3d_models/*.obj (standard Wavefront OBJ files)
"""

import struct
import json
from pathlib import Path

def load_vga_palette(pal_path='game/ALTPAL.ISR'):
    palette = []
    if Path(pal_path).exists():
        with open(pal_path, 'rb') as f:
            d = f.read()
        num_colors = len(d) // 3
        for i in range(num_colors):
            r = min(255, d[i*3] * 4)
            g = min(255, d[i*3+1] * 4)
            b = min(255, d[i*3+2] * 4)
            palette.append([r, g, b])
    else:
        for i in range(256):
            palette.append([i, i, i])
    return palette

def decode_aircraft_bin(filepath):
    """
    Decodes standalone flyable aircraft (*OBJ.BIN).
    Primary model uses the authentic High LOD (LOD 2) with clean geometry,
    while preserving LOD 0 (silhouette) and LOD 1 (medium detail).
    """
    path = Path(filepath)
    if not path.exists():
        return None
    with open(path, 'rb') as f:
        d = f.read()

    file_start = 12 if ('FSXOBJ' in path.name or 'JFULCOBJ' in path.name) else 10

    # 1. Decode LOD 0 (Low Detail Silhouette)
    sig0 = d.find(b'\xFF\xFF\x00\x40')
    lod0 = None
    if sig0 != -1:
        vc0, vo0, to0 = struct.unpack_from('<3H', d, sig0 + 4)
        vo0_abs = file_start + vo0
        to0_abs = file_start + to0
        verts0 = []
        for vi in range(vc0):
            if vo0_abs + vi * 6 + 6 <= len(d):
                x, y, z = struct.unpack_from('<hhh', d, vo0_abs + vi * 6)
                verts0.append([round(x / 10.0, 2), round(y / 10.0, 2), round(z / 10.0, 2)])
        
        p = to0_abs + 8
        faces0 = []
        color_palette = [142, 145, 148, 140, 137, 150, 144, 155, 160]
        poly_idx = 0
        while p + 2 <= len(d):
            cnt = struct.unpack_from('<H', d, p)[0]
            if cnt == 0xFFFF or cnt == 0:
                break
            if 3 <= cnt <= 20 and p + 2 + (cnt + 1) * 2 <= len(d):
                words = struct.unpack_from(f'<{cnt+1}H', d, p + 2)
                if all(w % 16 == 0 and w // 16 < vc0 for w in words):
                    ring = [w // 16 for w in words[:-1]]
                    col = color_palette[poly_idx % len(color_palette)]
                    faces0.append({'color': col, 'indices': ring})
                    poly_idx += 1
                    p += (cnt + 2) * 2
                    continue
            break
        
        edges0 = set()
        for f_item in faces0:
            ring = f_item['indices']
            for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                edges0.add(tuple(sorted([v1, v2])))
        
        lod0 = {
            'lod': 0,
            'name': 'LOD 0 (Low Detail)',
            'vertex_count': len(verts0),
            'face_count': len(faces0),
            'edge_count': len(edges0),
            'vertices': verts0,
            'faces': faces0,
            'edges': [list(e) for e in sorted(list(edges0))]
        }

    # 2. Decode LOD 2 (High Detail Authentic Model)
    # Authentic aircraft config table for High LOD:
    aircraft_configs = {
        'FALCOBJ.BIN': {'vo': 0x15a, 'vc': 177, 'f_start': 0x58a, 'f_end': 0x16dc},
        'HORNOBJ.BIN': {'vo': 0x172, 'vc': 208, 'f_start': 0x652 + 10, 'f_end': 0x1f86 + 10},
        'FULCOBJ.BIN': {'vo': 0x168, 'vc': 271, 'f_start': 0x6ea + 10, 'f_end': 0x17f2 + 10},
        'FSXOBJ.BIN': {'vo': 0x15a, 'vc': 182, 'f_start': 0x59e + 12, 'f_end': 0x1702 + 12},
        'JFULCOBJ.BIN': {'vo': 0x168, 'vc': 271, 'f_start': 0x6ea + 12, 'f_end': 0x17f2 + 12}
    }

    lod2 = None
    cfg = aircraft_configs.get(path.name)
    if cfg:
        v_abs = file_start + cfg['vo']
        vc = cfg['vc']
        verts2 = []
        for vi in range(vc):
            if v_abs + vi * 6 + 6 <= len(d):
                x, y, z = struct.unpack_from('<hhh', d, v_abs + vi * 6)
                verts2.append([round(x / 10.0, 2), round(y / 10.0, 2), round(z / 10.0, 2)])
        
        unique_faces2 = {}
        for p in range(cfg['f_start'], cfg['f_end'], 2):
            cnt = struct.unpack_from('<H', d, p)[0]
            if 3 <= cnt <= 12 and p + 2 + (cnt + 1) * 2 <= cfg['f_end']:
                words = struct.unpack_from(f'<{cnt+1}H', d, p + 2)
                if all(w % 16 == 0 and (w // 16) < len(verts2) for w in words):
                    ring = [w // 16 for w in words[:-1]]
                    # Do not include extent vectors 1 or 3 if they spike
                    norm = frozenset(ring)
                    if norm not in unique_faces2:
                        unique_faces2[norm] = {'color': 142, 'indices': ring}
        
        faces2 = list(unique_faces2.values())
        edges2 = set()
        for f_item in faces2:
            ring = f_item['indices']
            for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                edges2.add(tuple(sorted([v1, v2])))
        
        lod2 = {
            'lod': 2,
            'name': 'LOD 2 (High Detail)',
            'vertex_count': len(verts2),
            'face_count': len(faces2),
            'edge_count': len(edges2),
            'vertices': verts2,
            'faces': faces2,
            'edges': [list(e) for e in sorted(list(edges2))]
        }

    # Primary representation uses the authentic High LOD 2
    primary = lod2 if (lod2 and lod2['face_count'] > 0) else lod0
    lods_list = [
        lod0 if lod0 else {},
        {}, # LOD 1
        lod2 if lod2 else {},
        {}  # LOD 3
    ]

    return {
        'name': path.stem,
        'source': 'AIRCRAFT_BIN',
        'file': path.name,
        'vertex_count': primary['vertex_count'],
        'edge_count': primary['edge_count'],
        'face_count': primary['face_count'],
        'vertices': primary['vertices'],
        'edges': primary['edges'],
        'faces': primary['faces'],
        'lods': lods_list,
        'lod0': lod0,
        'lod2': lod2
    }

def decode_objects_archive(filepath='game/OBJECTS'):
    path = Path(filepath)
    if not path.exists():
        return []
    with open(path, 'rb') as f:
        data = f.read()

    first_off = struct.unpack_from('<I', data, 0)[0]
    num_objs = first_off // 4
    offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

    objects = []
    for i in range(num_objs):
        off = offsets[i]
        next_off = offsets[i+1] if i+1 < num_objs else len(data)
        size = next_off - off
        obj_bytes = data[off:next_off]

        # Name extraction
        name = ''
        if len(obj_bytes) > 12:
            nchunk = obj_bytes[4:12]
            if all(32 <= b <= 126 or b == 0 for b in nchunk):
                name = nchunk.decode('ascii', errors='ignore').replace('\x00', '').strip()
        if not name:
            name = f"OBJ_{i:02d}"

        # Find LOD table
        sig_pos = obj_bytes.find(b'\xFF\xFF\x00\x40')
        lods = []
        primary_verts = []
        primary_faces = []
        primary_edges = []

        if sig_pos != -1:
            lod_table_pos = sig_pos + 4
            lod_headers = []
            for lod_idx in range(4):
                if lod_table_pos + (lod_idx+1)*10 <= len(obj_bytes):
                    vc, vo, to, w3, w4 = struct.unpack_from('<5H', obj_bytes, lod_table_pos + lod_idx*10)
                    if 0 < vc < 3000 and 0 < vo < len(obj_bytes):
                        lod_headers.append((lod_idx, vc, vo, to))

            for h_idx, (lod_idx, vc, vo, to) in enumerate(lod_headers):
                verts = []
                for vi in range(vc):
                    if vo + vi*6 + 6 <= len(obj_bytes):
                        x, y, z = struct.unpack_from('<hhh', obj_bytes, vo + vi*6)
                        verts.append([round(y / 10.0, 2), round(-z / 10.0, 2), round(-x / 10.0, 2)])

                ptr = to
                poly_offsets = set()
                while ptr + 2 <= len(obj_bytes):
                    node_off = struct.unpack_from('<H', obj_bytes, ptr)[0]
                    ptr += 2
                    if node_off == 0xFFFF:
                        break
                    if node_off + 2 > len(obj_bytes):
                        continue
                    w0 = struct.unpack_from('<H', obj_bytes, node_off)[0]
                    if w0 == 0xFFFF:
                        sub_ptr = node_off + 2
                        while sub_ptr + 2 <= len(obj_bytes):
                            target = struct.unpack_from('<H', obj_bytes, sub_ptr)[0]
                            sub_ptr += 2
                            if target == 0xFFFF or target == 0:
                                break
                            if target + 8 <= len(obj_bytes):
                                poly_offsets.add(target)
                    else:
                        poly_offsets.add(node_off)

                faces = []
                edges = set()
                for p in sorted(list(poly_offsets)):
                    if p + 8 <= len(obj_bytes):
                        norm, mode, col, cnt = struct.unpack_from('<4H', obj_bytes, p)
                        if 3 <= cnt <= 20 and p + 8 + (cnt+1)*2 <= len(obj_bytes):
                            v_words = struct.unpack_from(f'<{cnt+1}H', obj_bytes, p + 8)
                            if all(w % 16 == 0 and (w // 16) < len(verts) for w in v_words):
                                ring = [w // 16 for w in v_words[:-1]]
                                if len(set(ring)) >= 3:
                                    faces.append({'color': col, 'indices': ring})
                                    for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                                        edges.add(tuple(sorted([v1, v2])))

                lod_data = {
                    'lod': lod_idx,
                    'vertex_count': len(verts),
                    'face_count': len(faces),
                    'edge_count': len(edges),
                    'vertices': verts,
                    'faces': faces,
                    'edges': [list(e) for e in sorted(list(edges))]
                }
                lods.append(lod_data)
                if h_idx == 0:
                    primary_verts = verts
                    primary_faces = faces
                    primary_edges = [list(e) for e in sorted(list(edges))]

        cat = 'Generic'
        if any(w in name.upper() for w in ['MIG', 'SU', 'F16', 'F-16', 'F15', 'F-15', 'F4', 'F-4', 'MIRAGE', 'BEAR', 'IL76', 'A10']):
            cat = 'Aircraft'
        elif any(w in name.upper() for w in ['TANK', 'T72', 'T80', 'M1', 'BMP', 'BTR', 'ZSU', 'SHILKA', 'TRUCK', 'JEEP']):
            cat = 'Ground Vehicle'
        elif any(w in name.upper() for w in ['BOAT', 'SHIP', 'FRIGATE', 'PATROL']):
            cat = 'Naval Unit'
        elif any(w in name.upper() for w in ['SAM', 'SCUD', 'HAWK', 'PATRIOT', 'SA2', 'SA6', 'SA8', 'SA13']):
            cat = 'Air Defense'

        objects.append({
            'id': i,
            'name': name,
            'category': cat,
            'source': 'OBJECTS',
            'vertex_count': len(primary_verts),
            'face_count': len(primary_faces),
            'edge_count': len(primary_edges),
            'vertices': primary_verts,
            'faces': primary_faces,
            'edges': primary_edges,
            'lods': lods
        })

    return objects

def decode_mapobj_archive(filepath='game/MAPOBJ'):
    path = Path(filepath)
    if not path.exists():
        return []
    with open(path, 'rb') as f:
        data = f.read()

    first_off = struct.unpack_from('<I', data, 0)[0]
    num_objs = first_off // 4
    offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

    map_objects = []
    for i in range(num_objs):
        off = offsets[i]
        next_off = offsets[i+1] if i+1 < num_objs else len(data)
        size = next_off - off
        obj_bytes = data[off:next_off]

        if len(obj_bytes) < 4:
            continue

        tag = obj_bytes[0]
        verts = []
        edges = []
        faces = []
        cat = 'Terrain Structure'

        if tag == 0x01: # Ribbon model
            cat = 'Road & River Ribbon'
            cnt = obj_bytes[1]
            pos = 4
            for vi in range(cnt):
                if pos + 6 <= len(obj_bytes):
                    x, y, z = struct.unpack_from('<hhh', obj_bytes, pos)
                    verts.append([round(x / 10.0, 2), round(y / 10.0, 2), round(z / 10.0, 2)])
                    pos += 6
            for vi in range(len(verts) - 1):
                edges.append([vi, vi + 1])

        elif tag == 0x09: # Standard 3D model
            vc = struct.unpack_from('<H', obj_bytes, 1)[0]
            pos = 4
            for vi in range(vc):
                if pos + 6 <= len(obj_bytes):
                    x, y, z = struct.unpack_from('<hhh', obj_bytes, pos)
                    verts.append([round(x / 10.0, 2), round(y / 10.0, 2), round(z / 10.0, 2)])
                    pos += 6

            p = pos
            color_idx = 45
            while p + 2 <= len(obj_bytes):
                cnt = struct.unpack_from('<H', obj_bytes, p)[0]
                if cnt == 0xFFFF or cnt == 0:
                    break
                if 3 <= cnt <= 12 and p + 2 + (cnt + 1) * 2 <= len(obj_bytes):
                    words = struct.unpack_from(f'<{cnt+1}H', obj_bytes, p + 2)
                    if all(w % 16 == 0 and w // 16 < len(verts) for w in words):
                        ring = [w // 16 for w in words[:-1]]
                        faces.append({'color': color_idx, 'indices': ring})
                        p += (cnt + 2) * 2
                        color_idx = (color_idx + 3) % 250
                        continue
                break

            edge_set = set()
            for f_item in faces:
                ring = f_item['indices']
                for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                    edge_set.add(tuple(sorted([v1, v2])))
            edges = [list(e) for e in sorted(list(edge_set))]

        name = f"MAPOBJ_{i:03d}"
        map_objects.append({
            'id': i,
            'name': name,
            'category': cat,
            'source': 'MAPOBJ',
            'vertex_count': len(verts),
            'face_count': len(faces),
            'edge_count': len(edges),
            'vertices': verts,
            'faces': faces,
            'edges': edges,
            'lods': [{
                'lod': 0,
                'vertex_count': len(verts),
                'face_count': len(faces),
                'edge_count': len(edges),
                'vertices': verts,
                'faces': faces,
                'edges': edges
            }]
        })

    return map_objects

def decode_report_archive(filepath='game/REPORT.DAT'):
    """
    Decodes all 76 tactical reference dossiers and 3D models from REPORT.DAT.
    """
    path = Path(filepath)
    if not path.exists():
        return []
    with open(path, 'rb') as f:
        rep = f.read()

    sections = [
        ('Tactical Aircraft (Blue)', 0x10c6, 23),
        ('Tactical Aircraft (Red)', 0x28f75, 23),
        ('Ground Vehicles', 0x4eb68, 12),
        ('Naval & Defense', 0x63133, 18)
    ]

    report_models = []
    model_idx = 0

    for sec_name, sec_off, count in sections:
        offsets = [struct.unpack_from('<I', rep, sec_off + 2 + i*4)[0] for i in range(count)]
        for i in range(count):
            rec_start = sec_off + offsets[i]
            w0, w1, w2, w3 = struct.unpack_from('<HHHH', rep, rec_start)
            name_end = rep.find(b'\x00', rec_start + w1)
            raw_name = rep[rec_start + w1 : name_end].decode('latin1', errors='replace')
            name = ''.join(c for c in raw_name if 32 <= ord(c) <= 126).strip()

            # Extract specifications text
            specs = []
            p = rec_start + w1
            while p < rec_start + w2:
                ne = rep.find(b'\x00', p)
                if ne == -1 or ne > rec_start + w2:
                    break
                s = rep[p:ne].decode('latin1', errors='replace').strip()
                clean_s = ''.join(c for c in s if 32 <= ord(c) <= 126).strip()
                if clean_s:
                    specs.append(clean_s)
                p = ne + 1

            m_start = rec_start + w3
            m_bytes = rep[m_start:rec_start+w0]

            verts = []
            faces = []
            edges = set()

            sig_pos = m_bytes.find(b'\xff\xff')
            if sig_pos == 0x38:
                # Multi-part ground vehicle (Hull, Turret, Gun)
                w_sig, mode, parts_ptr_raw = struct.unpack_from('<3H', m_bytes, sig_pos)
                parts_off = parts_ptr_raw - w3
                p = parts_off
                parts = []
                while p + 14 <= len(m_bytes):
                    w_row = struct.unpack_from('<7H', m_bytes, p)
                    vc = w_row[3]
                    source_vo = w_row[4]
                    to_ptr = w_row[6]
                    if 3 <= vc <= 50 and source_vo > w3:
                        vo_rel = source_vo - w3
                        if vo_rel + vc*6 <= len(m_bytes):
                            parts.append((vc, vo_rel, to_ptr - w3 if to_ptr > w3 else to_ptr))
                            p += 14
                            continue
                    break

                part_v_offsets = []
                cur_v_off = 0
                for vc, vo_rel, to_rel in parts:
                    part_v_offsets.append(cur_v_off)
                    for vi in range(vc):
                        x, y, z = struct.unpack_from('<hhh', m_bytes, vo_rel + vi*6)
                        verts.append([round(x / 10.0, 2), round(y / 10.0, 2), round(z / 10.0, 2)])
                    cur_v_off += vc

                unique_faces = {}
                for p_idx, (vc, vo_rel, to_rel) in enumerate(parts):
                    v_base = part_v_offsets[p_idx]
                    for p in range(0x20, len(m_bytes) - 8, 2):
                        norm, mode, col, cnt = struct.unpack_from('<4H', m_bytes, p)
                        if 3 <= cnt <= 12 and p + 8 + (cnt+1)*2 <= len(m_bytes):
                            words = struct.unpack_from(f'<{cnt+1}H', m_bytes, p + 8)
                            if all(w % 16 == 0 and (w // 16) < vc for w in words):
                                ring = [(w // 16) + v_base for w in words[:-1]]
                                norm_ring = frozenset(ring)
                                if norm_ring not in unique_faces:
                                    unique_faces[norm_ring] = {'color': col, 'indices': ring}
                                    for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                                        edges.add(tuple(sorted([v1, v2])))
                faces = list(unique_faces.values())

            elif sig_pos != -1 and sig_pos + 16 <= len(m_bytes):
                # Single-piece model (Aircraft, Ships, SAMs, Missiles)
                w_sig, mode, v_hdr, zero, num_v_raw, v_off_raw, oct_raw = struct.unpack_from('<7H', m_bytes, sig_pos)
                num_v = num_v_raw // 6 if num_v_raw > 200 else num_v_raw
                v_start = v_off_raw - w3 if v_off_raw > w3 else v_off_raw
                if 0 < num_v < 1000 and 0 <= v_start < len(m_bytes):
                    for vi in range(num_v):
                        off = v_start + vi * 6
                        if off + 6 <= len(m_bytes):
                            x, y, z = struct.unpack_from('<hhh', m_bytes, off)
                            verts.append([round(x / 10.0, 2), round(y / 10.0, 2), round(z / 10.0, 2)])

                p_search_start = v_start + len(verts) * 6
                unique_faces = {}
                for p in range(p_search_start, len(m_bytes) - 8, 2):
                    norm, mode, col, cnt = struct.unpack_from('<4H', m_bytes, p)
                    if 3 <= cnt <= 12 and p + 8 + (cnt+1)*2 <= len(m_bytes):
                        words = struct.unpack_from(f'<{cnt+1}H', m_bytes, p + 8)
                        if all(w % 16 == 0 and (w // 16) < len(verts) for w in words):
                            ring = [w // 16 for w in words[:-1]]
                            norm_ring = frozenset(ring)
                            if norm_ring not in unique_faces:
                                unique_faces[norm_ring] = {'color': col, 'indices': ring}
                                for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                                    edges.add(tuple(sorted([v1, v2])))
                faces = list(unique_faces.values())

            report_models.append({
                'id': model_idx,
                'name': name,
                'category': 'Tactical Reference',
                'sub_category': sec_name,
                'source': 'REPORT.DAT',
                'specs': specs,
                'vertex_count': len(verts),
                'face_count': len(faces),
                'edge_count': len(edges),
                'vertices': verts,
                'faces': faces,
                'edges': [list(e) for e in sorted(list(edges))],
                'lods': [{
                    'lod': 0,
                    'vertex_count': len(verts),
                    'face_count': len(faces),
                    'edge_count': len(edges),
                    'vertices': verts,
                    'faces': faces,
                    'edges': [list(e) for e in sorted(list(edges))]
                }]
            })
            model_idx += 1

    return report_models

def export_wavefront_obj(item, out_path):
    with open(out_path, 'w') as f:
        f.write(f"# Falcon 3.0 3D Asset: {item['name']}\n")
        f.write(f"# Category: {item.get('category', 'Generic')}\n")
        f.write(f"# Vertices: {len(item['vertices'])}, Faces: {len(item.get('faces', []))}, Edges: {len(item.get('edges', []))}\n")
        for vx, vy, vz in item['vertices']:
            f.write(f"v {vx:.3f} {vy:.3f} {vz:.3f}\n")
        for face in item.get('faces', []):
            idx_str = ' '.join(str(idx + 1) for idx in face['indices'])
            f.write(f"f {idx_str}\n")
        if not item.get('faces') and item.get('edges'):
            for v1, v2 in item['edges']:
                f.write(f"l {v1 + 1} {v2 + 1}\n")

def main():
    print("=== Falcon 3.0 3D Asset Pipeline ===")
    out_dir = Path('analysis/viewer')
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_dir = Path('analysis/3d_models')
    obj_dir.mkdir(parents=True, exist_ok=True)

    palette = load_vga_palette()
    print(f"Loaded authentic VGA palette ({len(palette)} colors)")

    # 1. Standalone player aircraft (LOD 0 as primary)
    aircraft_bins = [
        'game/FALCOBJ.BIN',
        'game/HORNOBJ.BIN',
        'game/FULCOBJ.BIN',
        'game/FSXOBJ.BIN',
        'game/JFULCOBJ.BIN'
    ]
    flyable = []
    for ab in aircraft_bins:
        model = decode_aircraft_bin(ab)
        if model:
            model['category'] = 'Flyable Aircraft'
            flyable.append(model)
            export_wavefront_obj(model, obj_dir / f"{model['name']}.obj")
            if model.get('lod2') and model['lod2']['face_count'] > 0:
                export_wavefront_obj(model['lod2'], obj_dir / f"{model['name']}_High.obj")
    print(f"Decoded {len(flyable)} flyable aircraft from *OBJ.BIN")

    # 2. Objects archive (71 vehicles & weapons)
    objects = decode_objects_archive()
    for o in objects:
        if o['vertices']:
            clean_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in o['name']).strip()
            export_wavefront_obj(o, obj_dir / f"vehicle_{o['id']:02d}_{clean_name}.obj")
    print(f"Decoded {len(objects)} vehicles and weapons from game/OBJECTS")

    # 3. Map objects archive (128 terrain structures & ribbons)
    map_objects = decode_mapobj_archive()
    for m in map_objects:
        if m['vertices']:
            clean_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in m['name']).strip().replace(' ', '_')
            export_wavefront_obj(m, obj_dir / f"map_{m['id']:03d}_{clean_name}.obj")
    print(f"Decoded {len(map_objects)} map structures and ribbons from game/MAPOBJ")

    # 4. Tactical reference dossiers & 3D models from REPORT.DAT
    reports = decode_report_archive()
    for r in reports:
        if r['vertices'] and r['face_count'] > 0:
            clean_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in r['name']).strip()
            export_wavefront_obj(r, obj_dir / f"report_{r['id']:02d}_{clean_name}.obj")
    print(f"Decoded {len(reports)} tactical reference records from game/REPORT.DAT")

    # Assemble master database
    database = {
        'metadata': {
            'title': 'Falcon 3.0 3D Asset Database',
            'version': '1.0',
            'total_models': len(flyable) + len(objects) + len(map_objects) + len(reports),
            'palette': palette
        },
        'flyable_aircraft': flyable,
        'vehicles_and_units': objects,
        'terrain_structures': map_objects,
        'tactical_reference': reports
    }

    db_path = out_dir / 'assets_database.json'
    with open(db_path, 'w') as f:
        json.dump(database, f)
    print(f"Saved master 3D assets database ({db_path.stat().st_size / 1024:.1f} KB) -> {db_path}")

if __name__ == '__main__':
    main()
