import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

f16 = data[offsets[3]:offsets[4]]

sig_pos = f16.find(b'\xFF\xFF\x00\x40')
lod_table_pos = sig_pos + 4
vc, vo, to, w3, w4 = struct.unpack_from('<5H', f16, lod_table_pos)

print(f"LOD 0: vc={vc}, vo={hex(vo)}, to={hex(to)}, w3={hex(w3)}, w4={hex(w4)}")

# Let's inspect the bytes from to onwards:
# How does the original engine read polygons?
# Let's dump the 100 bytes around 'to':
print("Bytes at 'to':")
words = struct.unpack('<50H', f16[to:to+100])
for i in range(0, 50, 10):
    print(f"to+{i*2:02x}: " + " ".join(f"{w:04x}" for w in words[i:i+10]))
