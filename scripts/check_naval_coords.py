import struct

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])

# Nimitz: Obj 67
nimitz = data[offs[67]:offs[68]]
print(f"Nimitz length: {len(nimitz)}")
# LOD table in Nimitz:
# Let's find LOD table
for p in range(0x0010, 0x0040, 2):
    vc, vo, to, w3, w4 = struct.unpack_from('<5H', nimitz, p)
    if 20 <= vc <= 300 and vo < len(nimitz) and to < len(nimitz):
        print(f"Nimitz LOD at 0x{p:04x}: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}")
        # print first 5 verts
        for i in range(5):
            print(f"  v{i}: {struct.unpack_from('<3h', nimitz, vo + i * 6)}")
        break

# Lebed: Obj 66
lebed = data[offs[66]:offs[67]]
print(f"\nLebed length: {len(lebed)}")
for p in range(0x0010, 0x0040, 2):
    vc, vo, to, w3, w4 = struct.unpack_from('<5H', lebed, p)
    if 20 <= vc <= 300 and vo < len(lebed) and to < len(lebed):
        print(f"Lebed LOD at 0x{p:04x}: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}")
        for i in range(5):
            print(f"  v{i}: {struct.unpack_from('<3h', lebed, vo + i * 6)}")
        break
