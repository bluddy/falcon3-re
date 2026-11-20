import struct

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])
m113 = data[offs[36]:offs[37]]

# Check Row 0, Row 1, Row 2 at 0x0036
for r in range(3):
    pos = 0x0036 + r * 14
    row = struct.unpack_from('<7H', m113, pos)
    print(f"Row {r} at 0x{pos:04x}: {[f'0x{w:04x}' for w in row]}")
    # w1 is pointer to 1762 (0x06e2) etc.
    # What is at row[1]?
    ptr1 = row[1]
    if ptr1 < len(m113):
        words = struct.unpack_from('<8h', m113, ptr1)
        print(f"  Data at 0x{ptr1:04x}: {words}")
