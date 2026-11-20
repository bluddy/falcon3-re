import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

print('F16 in game/OBJECTS:')
print(f'Size word: {struct.unpack_from("<H", obj, 0)[0]} (total slice size: {size})')
print(f'Header words (0..32): {[hex(w) for w in struct.unpack_from("<16H", obj, 0)]}')
print(f'ASCII at 4: {obj[4:16]}')

p = 0
while True:
    idx = obj.find(b'\xff\xff', p)
    if idx == -1: break
    if idx + 14 <= len(obj):
        words = [hex(w) for w in struct.unpack_from("<6H", obj, idx+2)]
        print(f'  0xFFFF at offset {idx} (0x{idx:04x}): next words = {words}')
    p = idx + 2
