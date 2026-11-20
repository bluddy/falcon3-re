import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
obj = data[offsets[3]:offsets[4]] # F-16 in OBJECTS

sig = obj.find(b'\xff\xff\x00\x40')
vc, vo, to = struct.unpack_from('<3H', obj, sig + 4)

# 1. Authentic 58 polygons
octants = [0x0232, 0x0288, 0x02de, 0x0330, 0x0382, 0x03ce, 0x041a, 0x0466]
all_oct_nodes = set()
for i, oct_ptr in enumerate(octants):
    p = oct_ptr
    nodes = []
    while p + 2 <= len(obj):
        w = struct.unpack_from('<H', obj, p)[0]
        p += 2
        if w == 0xFFFF:
            if len(nodes) == 0: continue
            else: break
        if w < len(obj): nodes.append(w)
        if len(nodes) > 40: break
    all_oct_nodes.update(nodes)

p = to + 18
while p < 0x0288:
    w = struct.unpack_from('<H', obj, p)[0]
    all_oct_nodes.add(w)
    p += 2

auth_faces = []
for node_off in sorted(all_oct_nodes):
    if node_off >= len(obj): continue
    w4 = struct.unpack_from('<4H', obj, node_off)
    norm, mode, col, cnt = w4
    if 3 <= cnt <= 16 and node_off + 8 + (cnt+1)*2 <= len(obj):
        v_words = struct.unpack_from(f'<{cnt+1}H', obj, node_off + 8)
        if all(w % 16 == 0 and (w//16) < vc for w in v_words) and v_words[0] == v_words[-1]:
            ring = [w//16 for w in v_words[:-1]]
            auth_faces.append(tuple(sorted(ring)))

# 2. Linear scan faces
scan_faces = []
scan_dict = {}
for p in range(to, len(obj) - 8, 2):
    norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
    if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= len(obj):
        v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
        if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
            ring = [w // 16 for w in v_words[:-1]]
            k = tuple(sorted(ring))
            if k not in scan_dict:
                scan_dict[k] = p
                scan_faces.append(k)

auth_set = set(auth_faces)
scan_set = set(scan_faces)

print(f"Authentic faces: {len(auth_set)}")
print(f"Linear scan faces: {len(scan_set)}")
spurious = scan_set - auth_set
print(f"Spurious faces from linear scan: {len(spurious)}")
for s in spurious:
    print(f"  Spurious face at 0x{scan_dict[s]:04x}: {s}")
