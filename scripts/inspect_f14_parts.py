import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[0] # F14
size = offsets[1] - off
obj = data[off:off+size]

print(f"F14 size={len(obj)}, byte 2..3 = {hex(struct.unpack_from('<H', obj, 2)[0])}")
# Find all 0xffff 0x4000 or similar signatures
p = 0
while True:
    idx = obj.find(b'\xff\xff', p)
    if idx == -1: break
    w = struct.unpack_from('<H', obj, idx+2)[0]
    print(f"0xFFFF at 0x{idx:04x}: next word = 0x{w:04x}")
    p = idx + 2
