import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

def find_lod_table(obj):
    best_p = -1
    best_lods = []
    # Search for candidate LOD tables
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

def extract_faces(obj, vc, vo, to, next_to):
    # Try strictly bounded first
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
    
    # If strictly bounded gave 0 faces (e.g. tree pointers precede a shared pool), scan to end
    if not faces:
        for p in range(scan_start, len(obj) - 8, 2):
            norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
            if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= len(obj):
                v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
                if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                    ring = [w // 16 for w in v_words[:-1]]
                    k = tuple(sorted(ring))
                    if k not in unique:
                        unique.add(k)
                        faces.append({'color': col & 0xFF, 'indices': ring})
    return faces

for i in range(num_objs):
    off = offsets[i]
    next_off = offsets[i+1] if i+1 < num_objs else len(data)
    obj = data[off:next_off]
    name = obj[4:12].decode('ascii', errors='ignore').strip()
    if not name: name = f"OBJ_{i:02d}"
    byte2 = struct.unpack_from('<H', obj, 2)[0] if len(obj) >= 4 else 0
    
    is_multipart_tank = (byte2 == 0x010a and i != 38)
    if is_multipart_tank:
        continue
    
    table_p, lod_headers = find_lod_table(obj)
    if not lod_headers:
        continue
    
    lod0 = lod_headers[0]
    next_to = lod_headers[1][3] if len(lod_headers) > 1 else len(obj)
    if next_to <= lod0[3] or next_to > len(obj):
        next_to = len(obj)
    
    f0 = extract_faces(obj, lod0[1], lod0[2], lod0[3], next_to)
    if len(f0) == 0:
        print(f"[{i:02d}] {name:12s}: 0 FACES IN LOD 0")
    else:
        if i in [0, 1, 2, 3, 32, 37, 66, 67]:
            print(f"[{i:02d}] {name:12s}: vc={lod0[1]}, faces={len(f0)}")
