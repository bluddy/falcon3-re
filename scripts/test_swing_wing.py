import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])

swing_wing_ids = [0, 8, 22, 25, 26] # F14, F111, MIG23, SU24, MIG27

for idx in swing_wing_ids:
    obj = data[offsets[idx]:offsets[idx+1]]
    name = obj[4:12].decode('ascii', errors='ignore').strip()
    print(f"\n{name} (Obj {idx}):")
    # Check 0x70
    w = struct.unpack_from('<5H', obj, 0x70)
    print(f"  At 0x70: {[hex(x) for x in w]} -> vc={w[0]}, vo=0x{w[1]:04x}, to=0x{w[2]:04x}")
    # Also check other LODs
    for lod in range(4):
        if 0x70 + (lod+1)*10 <= len(obj):
            vc, vo, to, _, _ = struct.unpack_from('<5H', obj, 0x70 + lod*10)
            if 0 < vc < 500 and vo < len(obj) and to < len(obj):
                print(f"    LOD {lod}: vc={vc}, vo=0x{vo:04x}, to=0x{to:04x}")
