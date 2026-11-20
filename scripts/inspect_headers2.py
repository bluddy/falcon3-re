import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

for i in range(5):
    off = offsets[i]
    next_off = offsets[i+1] if i+1 < num_objs else len(data)
    obj = data[off:next_off]
    name = obj[4:12].decode('ascii', errors='ignore').replace('\x00', '').strip()
    print(f"\n--- Obj {i:2d} ({name:8s}) size={len(obj)} ---")
    words = [f"0x{w:04x}" for w in struct.unpack_from('<24H', obj, 0x40)]
    for row in range(3):
        print(f"  {0x40 + row*16:02x}: {' '.join(words[row*8:(row+1)*8])}")
