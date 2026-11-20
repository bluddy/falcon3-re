import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

vc, vo, to = struct.unpack_from('<3H', obj, 0x40)
print(f"F16: vc={vc}, vo={vo} (0x{vo:04x}), to={to} (0x{to:04x})")

raw_verts = [struct.unpack_from('<hhh', obj, vo + i*6) for i in range(vc)]

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
                faces.append({'color': col, 'indices': ring, 'raw_node': node_off})
            si += (cnt + 2) * 2
    else:
        cnt = struct.unpack_from('<H', data, si)[0]
        if 3 <= cnt <= 16 and si + 2 + (cnt + 1) * 2 <= len(data):
            v_words = struct.unpack_from(f'<{cnt+1}H', data, si + 2)
            if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
                ring = [w // 16 for w in v_words[:-1]]
                faces.append({'color': col, 'indices': ring, 'raw_node': node_off})
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

# Test 1: to as octant table starting at to (0x0222)
print("--- Test 1: to at 0x0222 ---")
faces1 = []
unique1 = set()
for octant in range(8):
    ptr = struct.unpack_from('<H', obj, to + octant * 2)[0]
    print(f"  octant {octant}: ptr=0x{ptr:04x}")
    for f in resolve_octant_or_node(obj, ptr, vc):
        k = tuple(sorted(f['indices']))
        if k not in unique1:
            unique1.add(k)
            faces1.append(f)
print(f"Total faces in Test 1: {len(faces1)}")

# Test 2: to as octant table starting at 0x0224
print("\n--- Test 2: to at 0x0224 ---")
faces2 = []
unique2 = set()
for octant in range(8):
    ptr = struct.unpack_from('<H', obj, 0x0224 + octant * 2)[0]
    print(f"  octant {octant}: ptr=0x{ptr:04x}")
    for f in resolve_octant_or_node(obj, ptr, vc):
        k = tuple(sorted(f['indices']))
        if k not in unique2:
            unique2.add(k)
            faces2.append(f)
print(f"Total faces in Test 2: {len(faces2)}")
