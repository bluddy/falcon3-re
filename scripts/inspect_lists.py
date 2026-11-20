import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

ptrs = [0x0232, 0x0288, 0x02de, 0x0330, 0x0382, 0x03ce, 0x041a]
for i in range(len(ptrs)):
    start = ptrs[i]
    end = ptrs[i+1] if i+1 < len(ptrs) else 0x0466
    words = [hex(w) for w in struct.unpack_from(f'<{(end-start)//2}H', obj, start)]
    print(f"List at 0x{start:04x}..0x{end:04x} (len={len(words)}): first={words[0]}, last={words[-1]}")
