"""
Falcon 3.0 Modular Ribbon & Ground Feature Extractor
Extracts modular 3D ribbon models (103..109) and object placement streams
from game/MAPOBJ and game/MAPOBJ.<THEATER> across all 8 theaters.
"""

import struct
import math
import json
from pathlib import Path

THEATERS = {
    'ISR': 'ISRAEL',
    'PAK': 'INDIA',
    'IRQ': 'KUWAIT',
    'KOR': 'KOREA',
    'NEL': 'NELLIS',
    'PAN': 'PANAMA',
    'HOK': 'JAPAN',
    'BOS': 'BOSNIA'
}

def load_ribbon_models(mapobj_path='game/MAPOBJ'):
    with open(mapobj_path, 'rb') as f:
        data = f.read()

    offsets = struct.unpack('<128I', data[:512])
    models = {}

    for m_idx in range(103, 110):
        off = offsets[m_idx]
        if off == 0 or off >= len(data):
            continue
        length = struct.unpack_from('<H', data, off)[0]
        mdata = data[off+2 : off+2+length]

        if m_idx == 103:
            # Model 103: standard 3D mesh format (crossroads ground pad)
            num_verts = struct.unpack_from('<H', mdata, 17)[0]
            vert_off = struct.unpack_from('<H', mdata, 19)[0]
        else:
            # Models 104..109: ribbon format (tag 0x01)
            num_verts = struct.unpack_from('<H', mdata, 9)[0]
            vert_off = struct.unpack_from('<H', mdata, 11)[0]

        verts = []
        for vi in range(num_verts):
            vx, vy, vz = struct.unpack_from('<hhh', mdata, vert_off + vi*6)
            verts.append((vx, vz))

        # Centerline / key points definition
        if m_idx == 108: # Straight along X
            centerline = [(-6400, 0), (6400, 0)]
        elif m_idx == 109: # Straight along Z
            centerline = [(0, -6400), (0, 6400)]
        elif m_idx in (105, 106, 107):
            # Take centerline midpoints of vertex pairs
            if m_idx == 106:
                # 90 deg curve: v0/v1 -> v2/v3 -> v4 -> v5/v6 -> v7 -> v8
                p0 = ((-2152 + -2152) // 2, (1000 + -1000) // 2)
                p1 = ((-1752 + -1752) // 2, (200 + -200) // 2)
                p2 = (1448, 200)
                p3 = ((384 + 384) // 2, (1000 + -1000) // 2)
                p4 = (1848, 0)
                p5 = (10808, 0)
                centerline = [p0, p1, p2, p3, p4, p5]
            elif m_idx == 105:
                # S-curve
                p0 = ((1000 + -1000) // 2, (-2152 + -2152) // 2)
                p1 = ((200 + -200) // 2, (-1752 + -1752) // 2)
                p2 = (200, 1448)
                p3 = ((1000 + -1000) // 2, (384 + 384) // 2)
                p4 = (0, 1848)
                p5 = (0, 10808)
                centerline = [p0, p1, p2, p3, p4, p5]
            else: # 107
                p0 = ((1000 + -1000) // 2, (2152 + 2152) // 2)
                p1 = ((200 + -200) // 2, (1752 + 1752) // 2)
                p2 = (200, -1448)
                p3 = ((1000 + -1000) // 2, (-384 + -384) // 2)
                p4 = (0, -1848)
                p5 = (0, -10808)
                centerline = [p0, p1, p2, p3, p4, p5]
        elif m_idx == 103:
            centerline = [(-3000, 0), (3000, 0), (0, -3000), (0, 3000)]
        else: # 104
            centerline = [(0, 0)]

        models[m_idx] = {
            'model_id': m_idx,
            'num_verts': num_verts,
            'verts': verts,
            'centerline': centerline
        }

    return models

def extract_theater_ribbons(theater_code, models):
    path = Path('game') / f'MAPOBJ.{theater_code}'
    if not path.exists():
        return []

    with open(path, 'rb') as f:
        data = f.read()

    blocks = struct.unpack('<64I', data[:0x100])
    placed_ribbons = []

    for b_idx, b_off in enumerate(blocks):
        if b_off == 0xFFFFFFFF or b_off >= len(data):
            continue
        subtiles = struct.unpack_from('<16H', data, b_off)
        for s_idx, s_off in enumerate(subtiles):
            abs_off = b_off + s_off
            if abs_off >= len(data):
                continue
            length = struct.unpack_from('<H', data, abs_off)[0]
            if length <= 16:
                continue
            payload = data[abs_off+18 : abs_off+2+length]
            p_len = len(payload)

            leaf_offsets = []
            visited = set()
            def walk(offset, depth):
                if offset in visited or offset >= p_len or depth > 12:
                    return
                visited.add(offset)
                cnt = payload[offset]
                if cnt & 0x80:
                    leaf_offsets.append(offset)
                    return
                if cnt == 0:
                    return
                for ci in range(cnt):
                    entry_off = offset + 1 + ci * 3
                    if entry_off + 3 <= p_len:
                        child = struct.unpack_from('<H', payload, entry_off + 1)[0]
                        walk(child, depth + 1)

            walk(0, 0)
            tile_y = (b_idx // 8) * 4 + s_idx // 4
            tile_x = (b_idx % 8) * 4 + s_idx % 4

            for loff in leaf_offsets:
                cnt = payload[loff] & 0x7F
                stream_start = loff + 1
                for item_i in range(cnt):
                    ioff = stream_start + item_i * 10
                    if ioff + 10 <= p_len:
                        x, y, flags = struct.unpack_from('<hhh', payload, ioff)
                        m_intact = payload[ioff + 6]
                        m_dmg = payload[ioff + 7]
                        rot = struct.unpack_from('<h', payload, ioff + 8)[0]

                        base_model = m_intact & 0x7F
                        if base_model in models:
                            angle = (rot & 0xFFFF) * (2.0 * math.pi / 65536.0)
                            cos_a = math.cos(angle)
                            sin_a = math.sin(angle)

                            # World centroid
                            gx = tile_x * 13108 + x
                            gy = tile_y * 13108 + y

                            # Transform centerline
                            c_pts = []
                            for cx, cz in models[base_model]['centerline']:
                                rx = cx * cos_a - cz * sin_a
                                rz = cx * sin_a + cz * cos_a
                                c_pts.append([round(gx + rx, 1), round(gy + rz, 1)])

                            placed_ribbons.append({
                                'tile': [tile_x, tile_y],
                                'pos': [gx, gy],
                                'model_raw': m_intact,
                                'model_base': base_model,
                                'damaged_model': m_dmg,
                                'rotation': rot,
                                'flags': flags,
                                'has_campaign_node': bool(m_intact & 0x80),
                                'centerline': c_pts
                            })

    return placed_ribbons

def assemble_continuous_chains(placed_ribbons, max_dist=2000.0):
    """
    Groups ribbon segments whose endpoints connect within max_dist.
    """
    chains = []
    # Segments that have at least 2 points in centerline
    segs = [r['centerline'] for r in placed_ribbons if len(r['centerline']) >= 2]
    
    # Simple chain builder
    used = set()
    for i, seg in enumerate(segs):
        if i in used:
            continue
        used.add(i)
        chain = list(seg)
        
        # Grow forward and backward
        growing = True
        while growing:
            growing = False
            for j, oseg in enumerate(segs):
                if j in used:
                    continue
                # Test chain tail vs oseg head
                d_th = math.hypot(chain[-1][0] - oseg[0][0], chain[-1][1] - oseg[0][1])
                if d_th < max_dist:
                    chain.extend(oseg)
                    used.add(j)
                    growing = True
                    break
                # Test chain tail vs oseg tail
                d_tt = math.hypot(chain[-1][0] - oseg[-1][0], chain[-1][1] - oseg[-1][1])
                if d_tt < max_dist:
                    chain.extend(list(reversed(oseg)))
                    used.add(j)
                    growing = True
                    break
                # Test chain head vs oseg tail
                d_ht = math.hypot(chain[0][0] - oseg[-1][0], chain[0][1] - oseg[-1][1])
                if d_ht < max_dist:
                    chain = list(oseg) + chain
                    used.add(j)
                    growing = True
                    break
                # Test chain head vs oseg head
                d_hh = math.hypot(chain[0][0] - oseg[0][0], chain[0][1] - oseg[0][1])
                if d_hh < max_dist:
                    chain = list(reversed(oseg)) + chain
                    used.add(j)
                    growing = True
                    break
        chains.append(chain)

    return chains

def main():
    models = load_ribbon_models()
    print(f"Loaded {len(models)} ribbon models from game/MAPOBJ")
    
    out_dir = Path('analysis/theater_maps')
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {}
    for code, full_name in THEATERS.items():
        ribbons = extract_theater_ribbons(code, models)
        chains = assemble_continuous_chains(ribbons)
        summary[code] = {
            'theater': full_name,
            'total_ribbon_placements': len(ribbons),
            'continuous_chains': len(chains),
            'ribbon_counts_by_model': {}
        }
        for r in ribbons:
            m = r['model_base']
            summary[code]['ribbon_counts_by_model'][m] = summary[code]['ribbon_counts_by_model'].get(m, 0) + 1

        out_json = out_dir / f'{code}_ribbon_features.json'
        with open(out_json, 'w') as f:
            json.dump({
                'theater': code,
                'name': full_name,
                'total_placements': len(ribbons),
                'chains': chains,
                'placements': ribbons
            }, f, indent=2)
        print(f"[{code}] {full_name:10s}: {len(ribbons):4d} ribbon segments, {len(chains):3d} continuous chains -> {out_json.name}")

    with open(out_dir / 'all_theaters_ribbon_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    main()
