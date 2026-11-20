import struct

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])

print("Index | Name     | byte2  | Total size | Type")
print("------+----------+--------+------------+----------------")
for i in range(len(offs)):
    obj = data[offs[i] : (offs[i+1] if i+1 < len(offs) else len(data))]
    name = obj[4:12].decode('latin1', errors='replace').strip()
    byte2 = struct.unpack_from('<H', obj, 2)[0] if len(obj) >= 4 else 0
    t_desc = ""
    if byte2 == 0x010a:
        t_desc = "Multi-part vehicle (Tank/APC)"
    elif byte2 == 0x0312:
        t_desc = "Swing-wing aircraft"
    elif byte2 == 0x0012:
        t_desc = "Aircraft (Fixed wing)"
    elif byte2 == 0x000a:
        t_desc = "Naval / Large unit"
    elif byte2 == 0x0002:
        t_desc = "Structure / Ground unit"
    else:
        t_desc = f"Other (0x{byte2:04x})"
    print(f" [{i:02d}] | {name:8s} | 0x{byte2:04x} | {len(obj):10d} | {t_desc}")
