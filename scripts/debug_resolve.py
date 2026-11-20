import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

vc, vo, to = struct.unpack_from('<3H', obj, 0x40)

ptr = 0x0288
print(f"Words at ptr=0x{ptr:04x}:")
words = struct.unpack_from('<16H', obj, ptr)
print([hex(w) for w in words])

# In resolve_octant_or_node:
w0 = struct.unpack_from('<H', obj, ptr)[0]
print(f"w0 = {hex(w0)}")
if w0 == 0xFFFF:
    print("w0 is 0xFFFF! So loop broke immediately if p started at ptr!")
