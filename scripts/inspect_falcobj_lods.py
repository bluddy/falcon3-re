import struct

with open('game/FALCOBJ.BIN', 'rb') as f:
    d = f.read()

sig = 28
lod_table = sig + 4
print("LOD table in FALCOBJ.BIN:")
for lod in range(6):
    if lod_table + lod*10 + 10 <= len(d):
        vc, vo, to, w3, w4 = struct.unpack_from('<5H', d, lod_table + lod*10)
        print(f"LOD {lod}: vc={vc}, vo={vo} ({vo:#x}), to={to} ({to:#x}), w3={w3} ({w3:#x}), w4={w4} ({w4:#x})")
