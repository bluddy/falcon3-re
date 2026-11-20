import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

for i in range(8):
    off = offsets[i]
    next_off = offsets[i+1] if i+1 < num_objs else len(data)
    obj = data[off:next_off]
    name = obj[4:12].decode('ascii', errors='ignore').replace('\x00', '').strip()
    sig = obj.find(b'\xff\xff\x00\x40')
    if sig != -1:
        vc, vo, to = struct.unpack_from('<3H', obj, sig + 4)
        print(f"Obj {i:2d} ({name:8s}): sig=0x{sig:04x}, vc={vc:3d}, vo=0x{vo:04x}, to=0x{to:04x}, vo+vc*6=0x{vo+vc*6:04x}")
        words_at_to = [f"0x{w:04x}" for w in struct.unpack_from('<10H', obj, to)]
        print(f"       words at to: {words_at_to}")
