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

print(f"Total vertices: {vc}")
print("\nCenterline vertices (y == 0):")
for vi, x, y, z in raw_verts:
    if y == 0:
        print(f"  v{vi:02d}: x={x:4d}, y={y:4d}, z={z:4d}")

stbd = [v for v in raw_verts if v[2] > 0]
port = [v for v in raw_verts if v[2] < 0]

print(f"\nStarboard (y > 0): {len(stbd)}, Port (y < 0): {len(port)}")

for s_vi, sx, sy, sz in stbd:
    matches = [p for p in port if p[2] == -sy]
    if len(matches) == 1:
        p_vi, px, py, pz = matches[0]
        dx = px - sx
        dz = pz - sz
        diff_str = "MATCH"
        if dx != 0 or dz != 0:
            diff_str = f"MISMATCH! dx={dx:4d}, dz={dz:4d} (port v{p_vi:02d} x={px}, z={pz} vs stbd v{s_vi:02d} x={sx}, z={sz})"
        print(f"Pair (v{s_vi:02d}, v{p_vi:02d}): y={sy:+3d} / {py:+3d} | {diff_str}")
    elif len(matches) == 0:
        print(f"Starboard v{s_vi:02d} (x={sx:4d}, y={sy:+3d}, z={sz:4d}) has NO exact -y port partner!")
    else:
        # multiple partners
        print(f"Starboard v{s_vi:02d} (x={sx:4d}, y={sy:+3d}, z={sz:4d}) matches multiple port: {[m[0] for m in matches]}")
