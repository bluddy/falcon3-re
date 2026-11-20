with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = int.from_bytes(data[:4], 'little')
offsets = [int.from_bytes(data[i*4:(i+1)*4], 'little') for i in range(first_off // 4)]

f16 = data[offsets[3]:offsets[4]]

# Search for 85, 110, 70, 250 in f16
for val in [85, 110, 70, 250]:
    b2 = val.to_bytes(2, 'little', signed=True)
    pos = 0
    found = []
    while True:
        p = f16.find(b2, pos)
        if p == -1: break
        found.append(hex(p))
        pos = p + 1
    print(f"Value {val} (0x{val&0xffff:04x}) appears at: {found}")
