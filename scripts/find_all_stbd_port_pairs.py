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

# Symmetrical pairs by polygon topology:
# Face 20 (stbd main) [6, 30, 16, 17, 11, 8]  <--> Face 22 (port main) [32, 7, 14, 15, 24, 25] (order reversed for normal)
# Face 24 (stbd flap) [11, 10, 9, 8]           <--> Face 26 (port flap) [15, 14, 13, 12]
# Face 30 (stbd in strake) [43, 20, 17, 16]   <--> Face 36 (port in strake) [46, 25, 24, 23]
# Face 32 (stbd out strake) [20, 19, 18, 17]  <--> Face 34 (port out strake) [23, 24, 22, 21]

pairs = [
    # (stbd_vi, port_vi, description)
    (6, 32, "wing root trailing"),
    (8, 7,  "wing root aft"),
    (11, 14, "flap root fwd"),
    (10, 13, "flap tip fwd"),
    (9, 12,  "flap tip aft"),
    (8, 15,  "flap root aft"),
    (16, 25, "wing root mid"),
    (17, 24, "wing LE / flap boundary"),
    (20, 23, "strake apex"),
    (18, 21, "wingtip LE"),
    (19, 22, "wingtip TE"),
    (43, 46, "chine root forward"),
]

print("Topological Symmetry Check (Starboard vs Port):")
for s_vi, p_vi, desc in pairs:
    s = raw_verts[s_vi]
    p = raw_verts[p_vi]
    # Expected: p.x == s.x, p.y == -s.y, p.z == s.z
    dx = p[1] - s[1]
    dy = p[2] - (-s[2])
    dz = p[3] - s[3]
    status = "OK" if (dx == 0 and dy == 0 and dz == 0) else f"ERR: dx={dx:+4d}, dy={dy:+4d}, dz={dz:+4d}"
    print(f"  {desc:25s} | Stbd v{s_vi:02d} ({s[1]:4d}, {s[2]:4d}, {s[3]:4d}) vs Port v{p_vi:02d} ({p[1]:4d}, {p[2]:4d}, {p[3]:4d}) -> {status}")
