import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

def parse_nodes_in_range(obj, start_p, end_p, vc):
    faces = []
    unique = set()
    p = start_p
    while p <= end_p - 8:
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
        p += 2
    return faces

print(f"Total objects in game/OBJECTS: {num_objs}")

successful = 0
for i in range(num_objs):
    off = offsets[i]
    next_off = offsets[i+1] if i+1 < num_objs else len(data)
    obj = data[off:next_off]
    name = obj[4:12].decode('ascii', errors='ignore').replace('\x00', '').strip()
    byte2 = struct.unpack_from('<H', obj, 2)[0]
    
    # Check if single piece or multi-part
    sig = obj.find(b'\xff\xff\x00\x40')
    if sig == -1:
        print(f"Obj {i:2d}: {name:12s} - No signature found")
        continue
    
    vc, vo, to = struct.unpack_from('<3H', obj, sig + 4)
    # Check if vc is reasonable
    if vc == 0 or vo >= len(obj) or vo + vc*6 > len(obj):
        # Could it be swing-wing or multi-part?
        # Check next words
        w_rec = struct.unpack_from('<6H', obj, sig + 4)
        print(f"Obj {i:2d}: {name:12s} - byte2=0x{byte2:04x}, sig=0x{sig:04x}, words={[hex(w) for w in w_rec]}")
        continue
    
    # Single piece model
    raw_verts = [struct.unpack_from('<hhh', obj, vo + j*6) for j in range(vc)]
    # Next LOD or end of obj
    next_to = struct.unpack_from('<H', obj, sig + 4 + 10)[0] if sig + 14 <= len(obj) else len(obj)
    if next_to == 0 or next_to > len(obj):
        next_to = len(obj)
    
    faces = parse_nodes_in_range(obj, to, next_to, vc)
    print(f"Obj {i:2d}: {name:12s} - vc={vc:3d}, vo=0x{vo:04x}, to=0x{to:04x} -> {len(faces):2d} faces")
    if len(faces) > 0:
        successful += 1

print(f"\nSuccessfully parsed {successful} / {num_objs} objects!")
