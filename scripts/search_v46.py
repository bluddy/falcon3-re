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

# Check all node words where (46 * 16) appears
w_46 = 46 * 16 # 736 = 0x02e0
print(f"Searching for 46*16 = {w_46} (0x{w_46:04x}):")

for p in range(0x4c0, 0x874, 2):
    norm, mode, col, cnt = struct.unpack_from('<4H', obj, p)
    if 3 <= cnt <= 16 and p + 8 + (cnt + 1) * 2 <= len(obj):
        v_words = struct.unpack_from(f'<{cnt+1}H', obj, p + 8)
        if w_46 in v_words:
            print(f"Node at 0x{p:04x}: cnt={cnt}, v_words={[hex(w) for w in v_words]}")
