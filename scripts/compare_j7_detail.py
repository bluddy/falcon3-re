import struct

# REPORT J7
rep_data = open('game/REPORT.DAT', 'rb').read()
sec_offsets = [struct.unpack_from('<I', rep_data, 4 + i * 4)[0] for i in range(4)]
s_off = sec_offsets[0]
rel = struct.unpack_from('<I', rep_data, s_off + 2 + 21 * 4)[0]
abs_off = s_off + rel
sz = struct.unpack_from('<H', rep_data, abs_off)[0]
j7_rep = rep_data[abs_off+2 : abs_off+2+sz]
rec_off = struct.unpack_from('<H', j7_rep, 4)[0]
vc_r, vo_r, to_r = struct.unpack_from('<3H', j7_rep, rec_off + 50)

# OBJECTS J7
obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
j7_obj = obj_data[offsets[57] : offsets[58]]
vc_o, vo_o, to_o = struct.unpack_from('<3H', j7_obj, 0x0040)

print(f"REPORT J7: vc={vc_r}, vo=0x{vo_r:04x}, to=0x{to_r:04x}")
print(f"OBJECTS J7: vc={vc_o}, vo=0x{vo_o:04x}, to=0x{to_o:04x}")

print("\n--- Comparing first 25 vertices ---")
print("Idx | REPORT.DAT (raw shorts)       | OBJECTS (raw shorts)        | Ratios (r/o)")
print("----+-------------------------------+-----------------------------+--------------")
for i in range(25):
    vr = struct.unpack_from('<3h', j7_rep, vo_r + i * 6)
    vo = struct.unpack_from('<3h', j7_obj, vo_o + i * 6)
    rx = f"{vr[0]/vo[0]:.2f}" if vo[0] != 0 else "-"
    ry = f"{vr[1]/vo[1]:.2f}" if vo[1] != 0 else "-"
    rz = f"{vr[2]/vo[2]:.2f}" if vo[2] != 0 else "-"
    print(f" {i:02d} | ({vr[0]:5d}, {vr[1]:5d}, {vr[2]:5d}) | ({vo[0]:5d}, {vo[1]:5d}, {vo[2]:5d}) | ({rx}, {ry}, {rz})")
