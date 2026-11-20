import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

for ptr in [0x0232, 0x0288, 0x02de, 0x0330, 0x0382, 0x03ce, 0x041a]:
    words = [hex(w) for w in struct.unpack_from('<10H', obj, ptr)]
    print(f"ptr 0x{ptr:04x}: {words}")
