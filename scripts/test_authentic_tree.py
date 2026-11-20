import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
obj = data[offsets[3]:offsets[4]] # F-16 in OBJECTS

sig = obj.find(b'\xff\xff\x00\x40')
vc, vo, to = struct.unpack_from('<3H', obj, sig + 4)
print(f"F-16: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}")

def parse_node(data, node_off, vc):
    if node_off + 4 > len(data):
        return []
    flags = struct.unpack_from('<H', data, node_off)[0]
    if flags & 0x4000:
        return []
    col = data[node_off + 2]
    has_sub = bool(flags & 0x1000)
    si = node_off + 4
    faces = []
    if has_sub:
        while si + 2 <= len(data):
            cnt = struct.unpack_from('<H', data, si)[0]
            if cnt == 0xFFFF or not (3 <= cnt <= 16):
                break
            if si + 2 + (cnt + 1) * 2 > len(data):
                break
            v_words = struct.unpack_from(f'<{cnt+1}H', data, si + 2)
            if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
                ring = [w // 16 for w in v_words[:-1]]
                faces.append({'color': col, 'indices': ring})
            si += (cnt + 2) * 2
    else:
        cnt = struct.unpack_from('<H', data, si)[0]
        if 3 <= cnt <= 16 and si + 2 + (cnt + 1) * 2 <= len(data):
            v_words = struct.unpack_from(f'<{cnt+1}H', data, si + 2)
            if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
                ring = [w // 16 for w in v_words[:-1]]
                faces.append({'color': col, 'indices': ring})
    return faces

def resolve_octant_or_node(data, ptr, vc):
    if ptr + 4 > len(data):
        return []
    w0 = struct.unpack_from('<H', data, ptr)[0]
    w2 = struct.unpack_from('<H', data, ptr + 4)[0] if ptr + 6 <= len(data) else 0
    if (w0 & 0x00FF) < 10 and (3 <= w2 <= 16 or w2 == 0xFFFF):
        return parse_node(data, ptr, vc)
    else:
        p = ptr
        faces = []
        while p + 2 <= len(data):
            node = struct.unpack_from('<H', data, p)[0]
            p += 2
            if node == 0xFFFF:
                break
            faces.extend(parse_node(data, node, vc))
        return faces

# Check octants
faces = []
unique = set()
# What is at 'to'? In F-16, to = 0x0222.
# At 0x0222: w0 = 0x00b4 (bounding box?), w1 = 0x0232 (pointer to octants?)
# Let's check both to (0x0222) and to+2 (0x0224) and 0x0232:
print(f"At to (0x{to:04x}): words={[hex(w) for w in struct.unpack('<8H', obj[to:to+16])]}")
octant_table_ptr = struct.unpack_from('<H', obj, to + 2)[0]
print(f"Octant table ptr at to+2: 0x{octant_table_ptr:04x}")
for octant in range(8):
    ptr = struct.unpack_from('<H', obj, octant_table_ptr + octant * 2)[0]
    f_oct = resolve_octant_or_node(obj, ptr, vc)
    print(f"  Octant {octant} (ptr=0x{ptr:04x}): {len(f_oct)} faces")
    for f in f_oct:
        k = tuple(sorted(f['indices']))
        if k not in unique:
            unique.add(k)
            faces.append(f)

print(f"\nTotal authentic faces extracted via tree: {len(faces)}")
