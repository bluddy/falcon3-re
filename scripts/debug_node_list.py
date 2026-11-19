import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

f16 = data[offsets[3]:offsets[4]]

sig_pos = f16.find(b'\xFF\xFF\x00\x40')
lod_table_pos = sig_pos + 4
vc, vo, to, w3, w4 = struct.unpack_from('<5H', f16, lod_table_pos)

ptr = to
while ptr + 2 <= len(f16):
    node_off = struct.unpack_from('<H', f16, ptr)[0]
    ptr += 2
    if node_off == 0xFFFF:
        print(f"End of table at {hex(ptr-2)}")
        break
    if node_off >= len(f16):
        print(f"Out of bounds node_off {hex(node_off)}")
        continue
    flags = struct.unpack_from('<H', f16, node_off)[0]
    color = f16[node_off + 2]
    flags2 = f16[node_off + 3]
    has_sublist = bool(flags & 0x1000)
    print(f"ptr={hex(ptr-2)} -> node_off={hex(node_off)}, flags=0x{flags:04x}, col={color}, sublist={has_sublist}")
    # Inspect first 10 words at node_off
    words = struct.unpack_from('<10H', f16, node_off)
    print("   words: " + " ".join(f"{w:04x}" for w in words))
