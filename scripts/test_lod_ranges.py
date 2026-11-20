import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
obj = data[offsets[3]:offsets[4]] # F-16 in OBJECTS

sig = obj.find(b'\xff\xff\x00\x40')
table_p = sig + 4

lods = []
for lod_idx in range(4):
    vc, vo, to, w3, w4 = struct.unpack_from('<5H', obj, table_p + lod_idx * 10)
    next_to = struct.unpack_from('<H', obj, table_p + (lod_idx + 1) * 10 + 4)[0] if lod_idx + 1 < 4 else len(obj)
    if next_to == 0 or next_to > len(obj) or next_to <= to:
        next_to = len(obj)
    print(f"LOD {lod_idx}: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}, next_to=0x{next_to:04x}")
    
    # Scan ONLY between to and next_to:
    faces = []
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
                    faces.append({'col': col & 0xFF, 'ring': ring, 'off': p})
    
    print(f"  -> Extracted {len(faces)} faces strictly within LOD {lod_idx} range [0x{to:04x}..0x{next_to:04x}]")
