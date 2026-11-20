import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
obj = data[offsets[3]:offsets[4]] # F-16 in OBJECTS

sig = obj.find(b'\xff\xff\x00\x40')
vc, vo, to = struct.unpack_from('<3H', obj, sig + 4)

octants = [0x0232, 0x0288, 0x02de, 0x0330, 0x0382, 0x03ce, 0x041a, 0x0466]
all_oct_nodes = set()
for i, oct_ptr in enumerate(octants):
    p = oct_ptr
    # read words until 0xFFFF or until next octant
    nodes = []
    while p + 2 <= len(obj):
        w = struct.unpack_from('<H', obj, p)[0]
        p += 2
        if w == 0xFFFF:
            # check if 0xFFFF is start or end
            if len(nodes) == 0:
                continue
            else:
                break
        if w < len(obj):
            nodes.append(w)
        if len(nodes) > 40:
            break
    print(f"Octant {i} (0x{oct_ptr:04x}): {len(nodes)} nodes: {[hex(x) for x in nodes[:8]]}")
    all_oct_nodes.update(nodes)

print(f"\nTotal unique nodes referenced across all 8 octants: {len(all_oct_nodes)}")

# Compare with the 40 nodes from 0x0234..0x0286:
p = to + 18 # 0x0234
direct_nodes = set()
while p < 0x0288:
    w = struct.unpack_from('<H', obj, p)[0]
    direct_nodes.add(w)
    p += 2

print(f"Direct nodes in 0x0234..0x0288: {len(direct_nodes)}")
print(f"Union of all nodes: {len(all_oct_nodes | direct_nodes)}")
missing = all_oct_nodes - direct_nodes
print(f"Nodes in octants but not in direct list: {len(missing)}: {[hex(x) for x in missing]}")
