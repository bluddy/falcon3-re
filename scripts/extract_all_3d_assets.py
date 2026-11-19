"""
Falcon 3.0 Comprehensive 3D Asset Decoder & Exporter
Extracts and parses all 3D assets:
- 71 Vehicles & Weapons from game/OBJECTS
- 128 Terrain Structures & Ribbons from game/MAPOBJ
- 5 Standalone Player Aircraft from game/*OBJ.BIN
- Authentic 256-color VGA Palette from game/ALTPAL.ISR
Outputs:
- analysis/viewer/assets_database.json (for web 3D viewer)
- analysis/3d_models/*.obj (standard Wavefront OBJ files)
"""

import struct
import json
from pathlib import Path

# Load authentic palette (256 colors, RGB 0..255)
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
        # Default grayscale/VGA fallback
        for i in range(256):
            palette.append([i, i, i])
    return palette

def decode_aircraft_bin(filepath):
    path = Path(filepath)
    if not path.exists():
        return None
    with open(path, 'rb') as f:
        d = f.read()
    v_count, l_count = struct.unpack_from('<HH', d, 2)
    v_start = 0xA0  # Authentic 0xA0 vertex offset
    verts = []
    for vi in range(v_count):
        if v_start + vi * 6 + 6 <= len(d):
            x, y, z = struct.unpack_from('<hhh', d, v_start + vi*6)
            # Aviation NED (X_fwd, Y_right, Z_down) to standard OpenGL 3D (X_right, Y_up, Z_fwd):
            verts.append([round(y / 10.0, 2), round(-z / 10.0, 2), round(-x / 10.0, 2)])
    
    l_start = v_start + v_count * 6
    edges = []
    for li in range(l_count):
        if l_start + li * 4 + 4 <= len(d):
            v1_raw, v2_raw = struct.unpack_from('<hh', d, l_start + li*4)
            v1 = v_count + v1_raw if v1_raw < 0 else v1_raw
            v2 = v_count + v2_raw if v2_raw < 0 else v2_raw
            if 0 <= v1 < len(verts) and 0 <= v2 < len(verts):
                edges.append([v1, v2])

    return {
        'name': path.stem,
        'source': 'AIRCRAFT_BIN',
        'file': path.name,
        'vertex_count': len(verts),
        'edge_count': len(edges),
        'face_count': 0,
        'vertices': verts,
        'edges': edges,
        'faces': []
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
                lod_end = lod_headers[h_idx + 1][3] if h_idx + 1 < len(lod_headers) else len(obj_bytes)
                if lod_end > len(obj_bytes):
                    lod_end = len(obj_bytes)

                verts = []
                for vi in range(vc):
                    v_off = vo + vi * 6
                    if v_off + 6 <= len(obj_bytes):
                        x, y, z = struct.unpack_from('<hhh', obj_bytes, v_off)
                        # Fix F-16 nozzle & collar vertices (historical 1991 truncation & alignment in OBJECTS Chunk 3)
                        if 'F16' in name and lod_idx == 0:
                            if vi in (48, 49, 50, 51, 52, 69, 72):
                                x = -115 # Exhaust nozzle rim plane (v48 was 0x008c -> 0xff8c -116 in FSX)
                            elif vi in (4, 5, 30, 31, 32, 68, 71):
                                x = -80  # Afterburner collar base plane (v71 was 0x00b4 -> 0xffb4 -76, v4 was 0 -> -80)
                        # Aviation NED to OpenGL 3D:
                        verts.append([round(y / 10.0, 2), round(-z / 10.0, 2), round(-x / 10.0, 2)])

                # Authentic pointer table traversal reversed from FALCONCD.EXE (object_3d_project_and_draw)
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
                        # ObjectVisibilityNode (BSP / view-angle group node)
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

                faces = []
                for p in sorted(list(poly_offsets)):
                    if p + 8 <= len(obj_bytes):
                        norm, mode, col, cnt = struct.unpack_from('<4H', obj_bytes, p)
                        if 3 <= cnt <= 20 and p + 8 + (cnt+1)*2 <= len(obj_bytes):
                            v_words = struct.unpack_from(f'<{cnt+1}H', obj_bytes, p + 8)
                            if all(w % 16 == 0 and (w // 16) < len(verts) for w in v_words):
                                ring = [w // 16 for w in v_words[:-1]]
                                if len(set(ring)) >= 3:
                                    # Normalize triangle strip quads like [23, 24, 22, 21] to perimeter [23, 24, 21, 22]
                                    if len(ring) == 4 and ring == [23, 24, 22, 21]:
                                        ring = [23, 24, 21, 22]
                                    faces.append({'color': col, 'indices': ring})

                # Derive clean perimeter edges from polygon faces
                edges = set()
                for f_item in faces:
                    ring = f_item['indices']
                    for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                        edges.add(tuple(sorted([v1, v2])))
                edge_list = [list(e) for e in sorted(list(edges))]

                if lod_idx == 0 or not primary_verts:
                    primary_verts = verts
                    primary_faces = faces
                    primary_edges = edge_list

                lods.append({
                    'lod': lod_idx,
                    'vertex_count': len(verts),
                    'face_count': len(faces),
                    'edge_count': len(edge_list),
                    'vertices': verts,
                    'faces': faces,
                    'edges': edge_list
                })

        # Categorize
        cat = 'Vehicle / Aircraft'
        u_name = name.upper()
        if any(x in u_name for x in ['M60', 'AMX', 'M113', 'BTR', 'BDRM', 'WALID', 'ZSU', 'SCUD']):
            cat = 'Ground Vehicle'
        elif any(x in u_name for x in ['LCI', 'LST', 'LEBED', 'NIMITZ']):
            cat = 'Naval Unit'
        elif any(x in u_name for x in ['BGM', 'SHAHINE']):
            cat = 'Missile / Munition'
        elif any(x in u_name for x in ['TOWER', 'MEAT', 'STROBE']):
            cat = 'Airfield Equipment'
        else:
            cat = 'Aircraft'

        objects.append({
            'id': i,
            'name': name,
            'category': cat,
            'source': 'GAME_OBJECTS',
            'size': size,
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

    offsets = struct.unpack('<128I', data[:512])
    models = []

    NAMES_MAP = {
        0: 'Runway / Airfield Base',
        1: 'Runway Strip',
        2: 'Hardened Aircraft Bunker / Hangar',
        3: 'Control Tower',
        4: 'Aircraft Shelter',
        5: 'Airbase Building',
        6: 'Radar Dome Station',
        7: 'Fuel Storage Tank',
        8: 'Barracks Building',
        9: 'Command Headquarters',
        10: 'Communications Array',
        20: 'SAM Launcher Site',
        26: 'Suspension Bridge Segment',
        27: 'Girder Bridge Segment',
        28: 'Railway Trestle Bridge',
        29: 'Highway Overpass',
        103: 'Road Intersection Pad',
        104: 'Ribbon Terminal Connector',
        105: 'Modular Ribbon S-Curve',
        106: 'Modular Ribbon 90-Deg Turn',
        107: 'Modular Ribbon Opposing Curve',
        108: 'Modular Ribbon Straight (X-Axis)',
        109: 'Modular Ribbon Straight (Z-Axis)',
        110: 'Bomb Crater',
        111: 'Destroyed Ruin',
        112: 'Vegetation / Forest Cluster'
    }

    for m_idx in range(128):
        off = offsets[m_idx]
        if off == 0 or off >= len(data):
            continue
        length = struct.unpack_from('<H', data, off)[0]
        mdata = data[off+2 : off+2+length]
        tag = mdata[0]

        verts = []
        faces = []
        edges = []

        if tag == 0x01: # Ribbon model
            if len(mdata) >= 15:
                num_verts = struct.unpack_from('<H', mdata, 9)[0]
                vert_off = struct.unpack_from('<H', mdata, 11)[0]
                for vi in range(num_verts):
                    if vert_off + vi*6 + 6 <= len(mdata):
                        vx, vy, vz = struct.unpack_from('<hhh', mdata, vert_off + vi*6)
                        verts.append([round(vx / 10.0, 2), round(vy / 10.0, 2), round(vz / 10.0, 2)])
                
                # Connect vertices into ribbon edges
                if len(verts) >= 2:
                    for i in range(len(verts) - 1):
                        edges.append([i, i+1])
                # Quads/faces between adjacent vertex pairs
                if len(verts) >= 4:
                    for i in range(0, len(verts) - 3, 2):
                        faces.append({'color': 183, 'indices': [i, i+1, i+3, i+2]})

        elif tag == 0x09: # Standard 3D model
            vert_off = struct.unpack_from('<H', mdata, 13)[0] if len(mdata) > 15 else 21
            num_verts = struct.unpack_from('<H', mdata, 15)[0] if len(mdata) > 17 else 8
            
            # Sanity check
            if 0 < num_verts < 100 and 0 < vert_off < len(mdata):
                for vi in range(num_verts):
                    if vert_off + vi*6 + 6 <= len(mdata):
                        vx, vy, vz = struct.unpack_from('<hhh', mdata, vert_off + vi*6)
                        verts.append([round(vx / 10.0, 2), round(vy / 10.0, 2), round(vz / 10.0, 2)])

            # Scan polygon faces
            p = vert_off + len(verts) * 6
            visited = set()
            while p + 8 <= len(mdata):
                col, cnt = struct.unpack_from('<HH', mdata, p)
                if 1 <= col <= 255 and 3 <= cnt <= 8:
                    ring_off = p + 4
                    if ring_off + cnt * 2 <= len(mdata):
                        v_idx = []
                        valid_ring = True
                        for ki in range(cnt):
                            raw_v = struct.unpack_from('<H', mdata, ring_off + ki*2)[0]
                            if raw_v % 16 != 0:
                                valid_ring = False
                                break
                            vi = raw_v // 16
                            if vi >= len(verts):
                                valid_ring = False
                                break
                            v_idx.append(vi)
                        if valid_ring and len(set(v_idx)) >= 3 and p not in visited:
                            visited.add(p)
                            faces.append({'color': col, 'indices': v_idx})
                p += 2

            # Derive edges
            edge_set = set()
            for f_item in faces:
                ring = f_item['indices']
                for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                    edge_set.add(tuple(sorted([v1, v2])))
            edges = [list(e) for e in sorted(list(edge_set))]

        name = NAMES_MAP.get(m_idx, f"Structure_{m_idx:02d}")
        cat = 'Road & River Ribbon' if 103 <= m_idx <= 109 else 'Terrain Structure'

        models.append({
            'id': m_idx,
            'name': name,
            'category': cat,
            'source': 'GAME_MAPOBJ',
            'tag': tag,
            'size': length,
            'vertex_count': len(verts),
            'face_count': len(faces),
            'edge_count': len(edges),
            'vertices': verts,
            'faces': faces,
            'edges': edges
        })

    return models

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

    # 1. Standalone player aircraft
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

    # Assemble master database
    database = {
        'metadata': {
            'title': 'Falcon 3.0 3D Asset Database',
            'version': '1.0',
            'total_models': len(flyable) + len(objects) + len(map_objects),
            'palette': palette
        },
        'flyable_aircraft': flyable,
        'vehicles_and_units': objects,
        'terrain_structures': map_objects
    }

    db_path = out_dir / 'assets_database.json'
    with open(db_path, 'w') as f:
        json.dump(database, f)
    print(f"Saved master 3D assets database ({db_path.stat().st_size / 1024:.1f} KB) -> {db_path}")

if __name__ == '__main__':
    main()
