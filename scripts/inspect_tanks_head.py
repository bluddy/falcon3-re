import struct

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])

for obj_idx in [34, 35, 36]:
    obj = data[offs[obj_idx] : offs[obj_idx+1]]
    name = obj[4:12].decode('latin1', errors='replace').strip()
    print(f"\n=== Obj {obj_idx} ({name}) around 0x0088 - 0x00a0 ===")
    for p in range(0x0088, 0x00a4, 2):
        w_s = struct.unpack_from('<h', obj, p)[0]
        w_u = struct.unpack_from('<H', obj, p)[0]
        print(f"  0x{p:04x}: signed={w_s:6d}, hex=0x{w_u:04x}")
