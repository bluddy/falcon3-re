import struct

obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', obj_data[:first_off])
j7_obj = obj_data[offsets[57] : offsets[58]]

vc = 71
vo = 0x0068
to = 0x0212
next_to = 0x070c

faces = []
unique = set()
for p in range(to, next_to - 8, 2):
    norm, mode, col, cnt = struct.unpack_from('<4H', j7_obj, p)
    if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= next_to:
        v_words = struct.unpack_from(f'<{cnt+1}H', j7_obj, p + 8)
        if all(w % 16 == 0 and (w // 16) < vc for w in v_words) and v_words[0] == v_words[-1]:
            ring = [w // 16 for w in v_words[:-1]]
            k = tuple(sorted(ring))
            if k not in unique:
                unique.add(k)
                faces.append({'col': col & 0xFF, 'indices': ring})

print(f'Total faces found: {len(faces)}')
for i, f in enumerate(faces):
    if i < 10 or i >= len(faces) - 5:
        print(f'{i:02d}: col={f["col"]}, idx={f["indices"]}')
