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

# Scan every word in obj to see if it's a valid node!
valid_nodes = []
for p in range(0x400, len(obj) - 8, 2):
    norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
    if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= len(obj):
        v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
        if all(w % 16 == 0 and (w // 16) < vc for w in v_words):
            if v_words[0] == v_words[-1]: # closed polygon ring!
                valid_nodes.append((p, col & 0xFF, cnt, [w // 16 for w in v_words[:-1]]))

print(f"Total valid polygon nodes found by scanning all obj: {len(valid_nodes)}")
print("First 15 nodes:")
for p, col, cnt, ring in valid_nodes[:15]:
    print(f"  0x{p:04x}: col={col:3d}, cnt={cnt:2d}, ring={ring}")

print("Last 15 nodes:")
for p, col, cnt, ring in valid_nodes[-15:]:
    print(f"  0x{p:04x}: col={col:3d}, cnt={cnt:2d}, ring={ring}")
