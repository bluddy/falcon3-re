import struct

data = open('game/OBJECTS', 'rb').read()
first = struct.unpack_from('<I', data, 0)[0]
offs = struct.unpack(f'<{first//4}I', data[:first])
m113 = data[offs[36]:offs[37]]

print("=== M113 around 0x0180 - 0x01a5 ===")
for p in range(0x0180, 0x01a6, 2):
    w_s = struct.unpack_from('<h', m113, p)[0]
    w_u = struct.unpack_from('<H', m113, p)[0]
    print(f"  0x{p:04x}: signed={w_s:6d}, hex=0x{w_u:04x}")

print("\n=== M113 around 0x0480 - 0x04a5 ===")
for p in range(0x0480, 0x04a6, 2):
    w_s = struct.unpack_from('<h', m113, p)[0]
    w_u = struct.unpack_from('<H', m113, p)[0]
    print(f"  0x{p:04x}: signed={w_s:6d}, hex=0x{w_u:04x}")
