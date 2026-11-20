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

# Traverse all 8 octants
octants = [struct.unpack_from('<H', obj, 0x224 + i*2)[0] for i in range(8)]
print("8 Octant stream start pointers:", [hex(o) for o in octants])

node_ptrs = set()
for oct_idx, start_p in enumerate(octants):
    p = start_p
    # if leading 0xFFFF, skip
    if struct.unpack_from('<H', obj, p)[0] == 0xFFFF:
        p += 2
    count = 0
    while p + 2 <= len(obj):
        node = struct.unpack_from('<H', obj, p)[0]
        p += 2
        if node == 0xFFFF or node == 0:
            break
        if 0x400 <= node < len(obj):
            node_ptrs.add(node)
            count += 1
    print(f"  Octant {oct_idx} (0x{start_p:04x}): {count} nodes")

print(f"Total unique node pointers across all 8 octants: {len(node_ptrs)}")
