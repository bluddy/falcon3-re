import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
offsets = struct.unpack(f'<{first_off//4}I', data[:first_off])
obj = data[offsets[3]:offsets[4]] # F-16 in OBJECTS

sig = obj.find(b'\xff\xff\x00\x40')
vc, vo, to = struct.unpack_from('<3H', obj, sig + 4)

# Print words around 0x0222
print("Words at 0x0222:")
p = to
node_ptrs = []
while p + 2 <= len(obj):
    w = struct.unpack_from('<H', obj, p)[0]
    p += 2
    if w == 0xFFFF:
        break
    node_ptrs.append(w)
    if len(node_ptrs) > 50:
        break

print(f"Found {len(node_ptrs)} node pointers: {[hex(x) for x in node_ptrs]}")

for ptr in node_ptrs[:10]:
    if ptr + 16 <= len(obj):
        w_head = [hex(x) for x in struct.unpack('<8H', obj[ptr:ptr+16])]
        print(f"Node at 0x{ptr:04x}: {w_head}")
