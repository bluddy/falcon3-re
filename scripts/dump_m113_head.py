import struct

obj_data = open('game/OBJECTS', 'rb').read()
first_off = struct.unpack_from('<I', obj_data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', obj_data[:first_off])
m113_obj = obj_data[offsets[36] : offsets[37]]

print(f"Total size of Obj 36: {len(m113_obj)}")
for i in range(0, 0x100, 16):
    chunk = m113_obj[i:i+16]
    hex_str = " ".join(f"{b:02x}" for b in chunk)
    words = [struct.unpack_from('<H', chunk, j)[0] for j in range(0, len(chunk), 2)]
    words_str = " ".join(f"{w:5d}" for w in words)
    print(f"{i:04x}: {hex_str:<48} | {words_str}")
