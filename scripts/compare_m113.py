import struct
from pathlib import Path

# 1. REPORT.DAT M113
rep_data = open('game/REPORT.DAT', 'rb').read()
sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]
s_off = sec_offsets[2]
# Item 4
rel = struct.unpack_from('<I', rep_data, s_off + 2 + 4 * 4)[0]
abs_off = s_off + rel
sz = struct.unpack_from('<H', rep_data, abs_off)[0]
m113_rep = rep_data[abs_off+2 : abs_off+2+sz]

print("=== REPORT.DAT M113 ===")
rec_off = struct.unpack_from('<H', m113_rep, 4)[0]
print(f"rec_off: {rec_off} (0x{rec_off:x})")
# inspect around rec_off
for i in range(rec_off, min(rec_off + 100, len(m113_rep)), 2):
    w = struct.unpack_from('<H', m113_rep, i)[0]
    print(f"  +0x{i-rec_off:02x} (0x{i:04x}): 0x{w:04x} ({w})")

# 2. OBJECTS M113 (index 36)
obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
m113_obj = obj_data[offsets[36] : offsets[37]]

print("\n=== OBJECTS M113 (Obj 36) ===")
print(f"Total size: {len(m113_obj)}")
for i in range(0, min(100, len(m113_obj)), 2):
    w = struct.unpack_from('<H', m113_obj, i)[0]
    print(f"  0x{i:04x}: 0x{w:04x} ({w})")
