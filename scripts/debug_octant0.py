import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

print("Words in 0x0232 (until 0x0288):")
words = [hex(w) for w in struct.unpack_from(f'<{(0x288 - 0x232)//2}H', obj, 0x232)]
print(words)
