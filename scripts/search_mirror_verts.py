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

raw_verts = []
for vi in range(vc):
    x, y, z = struct.unpack_from('<hhh', f16, vo + vi * 6)
    raw_verts.append((vi, x, y, z))

stbd_verts = [6, 8, 11, 10, 9, 16, 17, 18, 19, 20, 43]

print("Searching for exact mirror vertices across all 74 vertices:")
for s_vi in stbd_verts:
    sx, sy, sz = raw_verts[s_vi][1:]
    target = (sx, -sy, sz)
    # search all verts
    matches = [v[0] for v in raw_verts if (v[1], v[2], v[3]) == target]
    close = [v[0] for v in raw_verts if v[2] == -sy and v[3] == sz]
    print(f"Stbd v{s_vi:02d} ({sx:4d}, {sy:4d}, {sz:4d}) -> Target ({target[0]:4d}, {target[1]:4d}, {target[2]:4d}):")
    print(f"    Exact matches: {matches}")
    print(f"    Same Y/Z: {[(v, raw_verts[v][1]) for v in close]}")
