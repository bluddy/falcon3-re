import struct

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])

for obj_id in [34, 35, 36, 41, 42, 43]:
    obj = data[offs[obj_id]:offs[obj_id+1]]
    name = obj[4:12].decode('latin1', errors='replace').strip()
    print(f"\n--- {name} (Obj {obj_id}) ---")
    p_row = 0x0036
    while p_row + 14 <= 0x0060:
        flags, r_mat, trans_ptr, vc, vo_h, w5, part_table_ptr = struct.unpack_from('<7H', obj, p_row)
        vo = vo_h + 2
        to = struct.unpack_from('<H', obj, part_table_ptr + 6)[0] if part_table_ptr + 8 <= len(obj) else vo + vc * 6
        if to > vo:
            vc_clamped = min(vc, (to - vo + 5) // 6)
        else:
            vc_clamped = vc
        print(f"  Part at 0x{p_row:02x}: vc={vc} -> clamped={vc_clamped}, vo=0x{vo:04x}, to=0x{to:04x}")
        p_row += 14
