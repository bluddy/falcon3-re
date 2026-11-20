import struct
import json

# 1. REPORT.DAT J7
rep_data = open('game/REPORT.DAT', 'rb').read()
sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]

j7_rep = None
j7_rep_name = ""
for s_idx, s_off in enumerate(sec_offsets):
    count = struct.unpack_from('<H', rep_data, s_off)[0]
    for i in range(count):
        rel = struct.unpack_from('<I', rep_data, s_off + 2 + i * 4)[0]
        abs_off = s_off + rel
        sz = struct.unpack_from('<H', rep_data, abs_off)[0]
        item = rep_data[abs_off+2 : abs_off+2+sz]
        text_off = struct.unpack_from('<H', item, 0)[0]
        snap_off = struct.unpack_from('<H', item, 2)[0] if len(item) > 2 else text_off + 200
        txt = item[text_off:min(len(item), snap_off)]
        specs = [s.decode('latin1', errors='replace').strip() for s in txt.split(b'\x00') if s.strip()]
        name = specs[0] if specs else ''
        if 'J-7' in name.upper() or 'J7' in name.upper() or 'F-7' in name.upper():
            print(f"Found in REPORT.DAT: section {s_idx}, item {i}, name: '{name}', item len: {len(item)}")
            j7_rep = item
            j7_rep_name = name
            break
    if j7_rep:
        break

# 2. OBJECTS J7 (Obj 57)
obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])

j7_obj = obj_data[offsets[57] : offsets[58]]
name_57 = j7_obj[4:12].decode('latin1', errors='replace').strip()
print(f"Found in OBJECTS: Obj 57, name: '{name_57}', len: {len(j7_obj)}")

# Inspect REPORT.DAT J7 3D record
rec_off = struct.unpack_from('<H', j7_rep, 4)[0]
print(f"REPORT J7 rec_off: 0x{rec_off:x}")
lod_off = rec_off + 50
vc_r, vo_r, to_r = struct.unpack_from('<3H', j7_rep, lod_off)
print(f"REPORT J7: vc={vc_r}, vo=0x{vo_r:x}, to=0x{to_r:x}")

# Inspect OBJECTS J7 3D record
# Let's inspect LOD table in OBJECTS J7
for p in range(0x0010, 0x0100, 2):
    vc, vo, to, w3, w4 = struct.unpack_from('<5H', j7_obj, p)
    if 10 <= vc <= 200 and vo < len(j7_obj) and to < len(j7_obj) and vo + vc * 6 <= to and w3 == 0 and w4 == 0:
        print(f"OBJECTS J7 LOD at 0x{p:04x}: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}")
        break
