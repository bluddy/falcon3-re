import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

def find_lod_table(obj):
    # Scan from 0x14 to min(0x200, len(obj)-20)
    best_p = -1
    best_lods = []
    for p in range(0x14, min(0x200, len(obj) - 10), 2):
        lods = []
        for lod_idx in range(4):
            if p + (lod_idx + 1) * 10 <= len(obj):
                vc, vo, to, w3, w4 = struct.unpack_from('<5H', obj, p + lod_idx * 10)
                if 2 <= vc <= 250 and 0x20 <= vo < len(obj) and vo + vc * 6 <= len(obj) and to < len(obj) and w3 == 0 and w4 == 0:
                    lods.append((vc, vo, to))
                else:
                    break
        if len(lods) > len(best_lods):
            best_lods = lods
            best_p = p
    return best_p, best_lods

for i in range(num_objs):
    off = offsets[i]
    next_off = offsets[i+1] if i+1 < num_objs else len(data)
    obj = data[off:next_off]
    name = obj[4:12].decode('ascii', errors='ignore').strip()
    if not name: name = f"OBJ_{i:02d}"
    byte2 = struct.unpack_from('<H', obj, 2)[0] if len(obj) >= 4 else 0
    
    if byte2 == 0x010a and i != 38:
        print(f"[{i:02d}] {name:12s}: Multi-part tank (byte2=0x010a)")
        continue
    
    pos, lods = find_lod_table(obj)
    if pos != -1 and len(lods) > 0:
        desc = ", ".join(f"LOD{idx}:({vc}v, vo=0x{vo:04x}, to=0x{to:04x})" for idx, (vc, vo, to) in enumerate(lods))
        print(f"[{i:02d}] {name:12s}: Table at 0x{pos:04x} ({len(lods)} LODs) -> {desc}")
    else:
        print(f"[{i:02d}] {name:12s}: NO TABLE FOUND (len={len(obj)}, byte2=0x{byte2:04x})")
