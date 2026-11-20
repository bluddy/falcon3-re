import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
o_f14 = data[offsets[0]:offsets[1]]

# Search for polygon nodes in F-14
poly_nodes = []
for p in range(0, len(o_f14) - 8, 2):
    norm, mode, col, cnt = struct.unpack_from('<4H', o_f14, p)
    if 3 <= cnt <= 12 and p + 8 + (cnt+1)*2 <= len(o_f14):
        v_words = struct.unpack_from(f'<{cnt+1}H', o_f14, p + 8)
        if all(w % 16 == 0 for w in v_words) and v_words[0] == v_words[-1]:
            indices = [w // 16 for w in v_words[:-1]]
            poly_nodes.append((p, col & 0xFF, indices))

print(f"Total polygon nodes found in F-14: {len(poly_nodes)}")
max_v = max(max(idx) for _, _, idx in poly_nodes)
print(f"Max vertex index referenced: {max_v}")
for p, col, idx in poly_nodes[:10]:
    print(f"  Node at 0x{p:04x}: col={col}, ring={idx}")
