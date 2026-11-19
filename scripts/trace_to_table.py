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

print(f"LOD 0 table offset: {hex(to)}")

# Let's read words from 'to' until 0xFFFF or until out of bounds:
ptr = to
indices = []
while ptr + 2 <= len(f16):
    w = struct.unpack_from('<H', f16, ptr)[0]
    ptr += 2
    if w == 0xFFFF:
        print(f"End of table at {hex(ptr-2)}: 0xFFFF")
        break
    indices.append(w)

print(f"Found {len(indices)} pointers in 'to' table:")
for idx, p in enumerate(indices[:20]):
    # inspect what is at offset p in f16
    if p < len(f16):
        sample = f16[p:p+20]
        hex_sample = " ".join(f"{b:02x}" for b in sample)
        print(f"[{idx:2d}] off={hex(p)}: {hex_sample}")
