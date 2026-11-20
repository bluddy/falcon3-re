import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])
off = offsets[3] # F16
size = offsets[4] - off
obj = data[off:off+size]

with open('memdump/MEMDUMP8_f16_model_viewer.BIN', 'rb') as f:
    mem = f.read()

print(f"Loaded MEMDUMP8: {len(mem)} bytes")
# Search for signature or exact byte sequence of F16
# e.g. vertices of F16:
vo = 102
vert_bytes = obj[vo : vo + 60] # first 10 vertices
idx = mem.find(vert_bytes)
print(f"Search for first 10 vertices: index = {idx} (0x{idx:08x})")

# Search for "F16" header
header_bytes = obj[4:16]
p = 0
found_headers = []
while True:
    idx = mem.find(header_bytes, p)
    if idx == -1: break
    found_headers.append(idx)
    p = idx + 1
print(f"Search for 'F16' header: {len(found_headers)} occurrences -> {[hex(h) for h in found_headers]}")
