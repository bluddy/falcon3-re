import struct

# REPORT.DAT M113
rep_data = open('game/REPORT.DAT', 'rb').read()
sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]
s_off = sec_offsets[2]
rel = struct.unpack_from('<I', rep_data, s_off + 2 + 4 * 4)[0]
m113_rep = rep_data[s_off + rel + 2 :]

print("=== REPORT.DAT Part records ===")
for p_rec in [0x1781, 0x178b, 0x1795]:
    words = struct.unpack_from('<5H', m113_rep, p_rec)
    print(f"0x{p_rec:04x}: vc={words[0]}, vo=0x{words[1]:04x}, to=0x{words[2]:04x}, w3=0x{words[3]:04x}, w4=0x{words[4]:04x}")

# OBJECTS M113
obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
m113_obj = obj_data[offsets[36] : offsets[37]]

print("\n=== OBJECTS Part records at 0x60, 0x6a, 0x74 ===")
for p_rec in [0x60, 0x6a, 0x74]:
    words = struct.unpack_from('<5H', m113_obj, p_rec)
    print(f"0x{p_rec:04x}: w0={words[0]} (0x{words[0]:04x}), w1=0x{words[1]:04x}, w2=0x{words[2]:04x}, w3=0x{words[3]:04x}, w4=0x{words[4]:04x}")
