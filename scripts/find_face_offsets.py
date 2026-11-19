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

# Same loop as extract_all_3d_assets.py:
p = to
faces = []
while p + 8 <= len(f16):
    w0, w1 = struct.unpack_from('<2H', f16, p)
    if 3 <= w1 <= 8 and 1 <= w0 <= 255:
        cnt = w1
        if p + 4 + (cnt+1)*2 + 2 <= len(f16):
            v_words = struct.unpack_from(f'<{cnt+1}H', f16, p + 4)
            if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
                ring = [w // 16 for w in v_words[:-1]]
                if len(set(ring)) >= 3:
                    faces.append((len(faces), hex(p), w0, cnt, ring))
                    p += (cnt + 4) * 2
                    continue
    p += 2

print(f"Total faces found by linear scan: {len(faces)}")
for fi, off, col, cnt, ring in faces:
    if fi in [44, 45, 12, 13, 14, 15, 16, 17, 18, 19]:
        print(f"Face {fi:2d} at offset {off}: col={col}, ring={ring}")
