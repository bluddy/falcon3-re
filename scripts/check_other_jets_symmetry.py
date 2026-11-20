import struct

with open('game/OBJECTS', 'rb') as f:
    data = f.read()

first_off = struct.unpack_from('<I', data, 0)[0]
num_objs = first_off // 4
offsets = struct.unpack(f'<{num_objs}I', data[:first_off])

def check_aircraft_symmetry(name_search):
    for i in range(num_objs):
        off = offsets[i]
        next_off = offsets[i+1] if i+1 < num_objs else len(data)
        chunk = data[off:next_off]
        name = chunk[4:12].decode('ascii', errors='ignore').strip('\x00 ')
        if name_search in name:
            sig_pos = chunk.find(b'\xFF\xFF\x00\x40')
            if sig_pos == -1: continue
            vc, vo, to, w3, w4 = struct.unpack_from('<5H', chunk, sig_pos + 4)
            verts = []
            for vi in range(vc):
                x, y, z = struct.unpack_from('<hhh', chunk, vo + vi * 6)
                verts.append((vi, x, y, z))
            
            stbd = [v for v in verts if v[2] > 0]
            port = [v for v in verts if v[2] < 0]
            
            perfect_mirror = 0
            for s in stbd:
                if any(p[1] == s[1] and p[2] == -s[2] and p[3] == s[3] for p in port):
                    perfect_mirror += 1
            print(f"Aircraft {name:8s} (Chunk {i:2d}, {vc:3d} verts): {len(stbd)} stbd, {len(port)} port -> {perfect_mirror}/{len(stbd)} exact mirrors ({perfect_mirror/len(stbd)*100:.1f}%)")

for ac in ['F15', 'F16', 'FA18', 'F4', 'KFIR', 'MIG29', 'SU27']:
    check_aircraft_symmetry(ac)
