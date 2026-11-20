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

octants = [struct.unpack_from('<H', obj, 0x224 + i*2)[0] for i in range(8)]
node_ptrs = set()
for start_p in octants:
    p = start_p
    if struct.unpack_from('<H', obj, p)[0] == 0xFFFF:
        p += 2
    while p + 2 <= len(obj):
        node = struct.unpack_from('<H', obj, p)[0]
        p += 2
        if node == 0xFFFF or node == 0:
            break
        if 0x400 <= node < len(obj):
            node_ptrs.add(node)

print(f"Analyzing all {len(node_ptrs)} nodes:")
for node in sorted(node_ptrs):
    words = [hex(w) for w in struct.unpack_from('<8H', obj, node)]
    norm, mode, col, cnt = struct.unpack_from('<4H', obj, node)
    v_words = []
    if cnt < 20 and node + 8 + (cnt+1)*2 <= len(obj):
        v_words = [hex(w) for w in struct.unpack_from(f'<{cnt+1}H', obj, node + 8)]
    print(f"Node 0x{node:04x}: col={col&0xFF:3d}, cnt={cnt:2d}, header={words[:4]}, verts={v_words}")
