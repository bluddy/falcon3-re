import struct

# 1. REPORT.DAT M113
rep_data = open('game/REPORT.DAT', 'rb').read()
sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]
s_off = sec_offsets[2]
rel = struct.unpack_from('<I', rep_data, s_off + 2 + 4 * 4)[0]
abs_off = s_off + rel
sz = struct.unpack_from('<H', rep_data, abs_off)[0]
m113_rep = rep_data[abs_off+2 : abs_off+2+sz]
rec_off = struct.unpack_from('<H', m113_rep, 4)[0]

print("=== REPORT.DAT M113 parts ===")
# In REPORT.DAT:
w_sig, mode, parts_ptr = struct.unpack_from('<3H', m113_rep, rec_off + 54)
print(f"rec_off: 0x{rec_off:x}, parts_ptr: 0x{parts_ptr:x}")

p = parts_ptr
part_idx = 0
while p + 14 <= len(m113_rep):
    w_row = struct.unpack_from('<7H', m113_rep, p)
    print(f"Row {part_idx} at 0x{p:04x}: {[f'0x{w:04x}' for w in w_row]}")
    part_rec_ptr = w_row[5]
    if part_rec_ptr != 0 and part_rec_ptr + 10 <= len(m113_rep):
        vc, vo, to, w3, w4 = struct.unpack_from('<5H', m113_rep, part_rec_ptr)
        print(f"  -> PartRec at 0x{part_rec_ptr:04x}: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}, w3=0x{w3:04x}, w4=0x{w4:04x}")
    p += 14
    part_idx += 1
    if w_row[0] == 0xffff or part_idx > 10:
        break

# 2. OBJECTS M113
obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
m113_obj = obj_data[offsets[36] : offsets[37]]

print("\n=== OBJECTS M113 rows ===")
# Look at offsets[36] header
# In OBJECTS, at 0x0034 is 0xffff? Or where?
# Let's see: at 0x0036 is 0x4000? Let's check rows of 7 words (14 bytes) starting at various places
for start in [0x36, 0x3a, 0x3c]:
    print(f"Trying start 0x{start:02x}:")
    for r in range(5):
        pos = start + r * 14
        if pos + 14 <= len(m113_obj):
            row = struct.unpack_from('<7H', m113_obj, pos)
            print(f"  Row {r} at 0x{pos:04x}: {[f'0x{w:04x}' for w in row]}")
