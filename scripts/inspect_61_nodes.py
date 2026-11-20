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
    nodes = []
    while p + 2 <= len(obj):
        w = struct.unpack_from('<H', obj, p)[0]
        p += 2
        if w == 0xFFFF:
            if len(nodes) == 0:
                continue
            else:
                break
        if w < len(obj):
            nodes.append(w)
        if len(nodes) > 40:
            break
    all_oct_nodes.update(nodes)

p = to + 18
while p < 0x0288:
    w = struct.unpack_from('<H', obj, p)[0]
    all_oct_nodes.add(w)
    p += 2

print(f"Total unique nodes: {len(all_oct_nodes)}")

poly_nodes = []
for node_off in sorted(all_oct_nodes):
    if node_off >= len(obj):
        continue
    w4 = struct.unpack_from('<4H', obj, node_off)
    norm, mode, col, cnt = w4
    if 3 <= cnt <= 16 and node_off + 8 + (cnt+1)*2 <= len(obj):
        v_words = struct.unpack_from(f'<{cnt+1}H', obj, node_off + 8)
        if all(w % 16 == 0 and (w//16) < vc for w in v_words) and v_words[0] == v_words[-1]:
            ring = [w//16 for w in v_words[:-1]]
            poly_nodes.append((node_off, col & 0xFF, ring))
        else:
            print(f"  Node 0x{node_off:04x}: cnt={cnt}, v_words={[w//16 for w in v_words]} FAIL")
    elif cnt == 2:
        print(f"  Node 0x{node_off:04x}: LINE primitive (cnt=2)")
    elif cnt == 1:
        print(f"  Node 0x{node_off:04x}: POINT primitive (cnt=1)")
    else:
        print(f"  Node 0x{node_off:04x}: other w4={[hex(x) for x in w4]}")

print(f"\nSuccessfully parsed {len(poly_nodes)} / {len(all_oct_nodes)} polygon nodes!")
