import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
obj = data[offsets[3]:offsets[4]] # F-16 in OBJECTS

sig = obj.find(b'\xff\xff\x00\x40')
vc, vo, to = struct.unpack_from('<3H', obj, sig + 4)
print(f"F-16: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}")

def parse_objects_node(data, node_off, vc):
    if node_off + 8 > len(data):
        return []
    norm, mode, col, cnt = struct.unpack_from('<4H', data, node_off)
    if not (3 <= cnt <= 16):
        return []
    if node_off + 8 + (cnt + 1) * 2 > len(data):
        return []
    v_words = struct.unpack_from(f'<{cnt+1}H', data, node_off + 8)
    if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
        ring = [w // 16 for w in v_words[:-1]]
        return [{'color': col & 0xFF, 'indices': ring, 'off': node_off}]
    return []

def resolve_objects_ptr(data, ptr, vc):
    if ptr + 8 > len(data):
        return []
    # Could be a direct node (cnt >= 3) or a list of node pointers (terminated by 0xFFFF)
    w = struct.unpack_from('<4H', data, ptr)
    # Check if direct node
    if 3 <= w[3] <= 16:
        # direct node
        return parse_objects_node(data, ptr, vc)
    else:
        # list of node pointers
        p = ptr
        faces = []
        visited = set()
        while p + 2 <= len(data):
            node = struct.unpack_from('<H', data, p)[0]
            p += 2
            if node == 0xFFFF or node == 0:
                break
            if node not in visited and node < len(data):
                visited.add(node)
                faces.extend(parse_objects_node(data, node, vc))
        return faces

octant_table_ptr = struct.unpack_from('<H', obj, to + 2)[0]
print(f"Octant table ptr: 0x{octant_table_ptr:04x}")

faces = []
unique = set()
for octant in range(8):
    ptr = struct.unpack_from('<H', obj, octant_table_ptr + octant * 2)[0]
    f_oct = resolve_objects_ptr(obj, ptr, vc)
    print(f"  Octant {octant} (ptr=0x{ptr:04x}): {len(f_oct)} faces")
    for f in f_oct:
        k = tuple(sorted(f['indices']))
        if k not in unique:
            unique.add(k)
            faces.append(f)

print(f"\nTotal authentic faces extracted via tree: {len(faces)}")
for f in faces[:10]:
    print(f"  Face at 0x{f['off']:04x}: col={f['color']}, ring={f['indices']}")
