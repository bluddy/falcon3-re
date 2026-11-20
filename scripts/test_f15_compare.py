import struct

rep_data = open('game/REPORT.DAT', 'rb').read()
sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]
s_off = sec_offsets[0]
rel = struct.unpack_from('<I', rep_data, s_off + 2 + 14 * 4)[0]
f15_rep = rep_data[s_off + rel + 2 :]
rec_off = struct.unpack_from('<H', f15_rep, 4)[0]
vc_r, vo_r, to_r = struct.unpack_from('<3H', f15_rep, rec_off + 50)

obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', obj_data[:first_off])
f15_obj = obj_data[offsets[2] : offsets[3]]
vc_o, vo_o, to_o = struct.unpack_from('<3H', f15_obj, 0x0040)

print(f'F-15: REPORT vc={vc_r}, vo=0x{vo_r:04x} | OBJECTS vc={vc_o}, vo=0x{vo_o:04x}')
matches = 0
for i in range(64):
    rx, ry, rz = struct.unpack_from('<3h', f15_rep, vo_r + i * 6)
    ox, oy, oz = struct.unpack_from('<3h', f15_obj, (vo_o + 2) + i * 6)
    ex, ey, ez = ox * 1.3, oy * 1.3, oz * 1.3
    close = abs(rx - ex) <= 1.5 and abs(ry - ey) <= 1.5 and abs(rz - ez) <= 1.5
    if close:
        matches += 1
    if i < 15 or not close:
        flag = 'OK' if close else 'DIFF'
        print(f'v{i:02d}: R=({rx:4d}, {ry:4d}, {rz:4d}) | O=({ox:4d}, {oy:4d}, {oz:4d}) | O*1.3=({ex:5.1f}, {ey:5.1f}, {ez:5.1f}) {flag}')

print(f'Total matching: {matches}/64')
