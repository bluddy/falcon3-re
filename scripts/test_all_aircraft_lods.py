import struct

obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', obj_data[:first_off])

def test_aircraft_lods(idx):
    chunk = obj_data[offsets[idx] : offsets[idx+1]]
    name = chunk[4:12].decode('ascii', errors='ignore').strip()
    print(f"\n==========================================")
    print(f"Testing Aircraft Obj {idx:02d} ({name}), size={len(chunk)}")
    print(f"==========================================")
    
    # Extract LOD headers
    lods = []
    for p in range(0x14, 0x100, 2):
        vc, vo_h, to_h, w3, w4 = struct.unpack_from('<5H', chunk, p)
        if 2 <= vc <= 250 and 0x20 <= vo_h < len(chunk) and w3 == 0 and w4 == 0:
            lods.append((len(lods), vc, vo_h + 2, to_h + 2))
    
    print(f"Found {len(lods)} LODs:")
    for lod_idx, vc, vo, to in lods:
        next_vo = lods[lod_idx+1][2] if lod_idx + 1 < len(lods) else len(chunk)
        if next_vo <= to or next_vo > len(chunk):
            next_vo = len(chunk)
            
        faces = []
        unique = set()
        for p in range(to, next_vo - 8, 2):
            norm, mode, col, cnt = struct.unpack_from('<4H', chunk, p)
            if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= next_vo:
                v_words = struct.unpack_from(f'<{cnt+1}H', chunk, p + 8)
                if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                    ring = [w // 16 for w in v_words[:-1]]
                    k = tuple(sorted(ring))
                    if k not in unique:
                        unique.add(k)
                        faces.append({'col': col & 0xFF, 'indices': ring})
        
        edges = set()
        for f in faces:
            ring = f['indices']
            for v1, v2 in zip(ring, ring[1:] + [ring[0]]):
                edges.add(tuple(sorted([v1, v2])))
                
        print(f"  LOD {lod_idx}: vc={vc:3d}, vo=0x{vo:04x}, to=0x{to:04x}, scan_to=0x{next_vo:04x} | faces={len(faces):3d}, edges={len(edges):3d}")

for obj_id in [57, 3, 2, 17, 18, 27]:
    test_aircraft_lods(obj_id)
