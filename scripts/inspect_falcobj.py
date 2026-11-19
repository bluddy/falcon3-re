import struct
from pathlib import Path

with open('game/FALCOBJ.BIN', 'rb') as f:
    d = f.read()

print("FALCOBJ.BIN length:", len(d))
v_count, l_count = struct.unpack_from('<HH', d, 2)
print("v_count:", v_count, "l_count:", l_count)
words = struct.unpack_from('<20H', d, 0)
print("First 20 words:", [f"{w:#06x}" for w in words])

# Search for any signatures or LOD tables in FALCOBJ.BIN
sig = d.find(b'\xff\xff\x00\x40')
print("sig 0x4000ffff in FALCOBJ.BIN:", sig)
