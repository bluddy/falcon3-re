import struct

with open('game/FalcObj.Bin', 'rb') as f:
    falc = f.read()

print(f"game/FalcObj.Bin size: {len(falc)} bytes")
print("First 64 bytes (hex):")
print(" ".join(f"{b:02x}" for b in falc[:64]))

# Find sig \xFF\xFF\x00\x40
sig_pos = falc.find(b'\xFF\xFF\x00\x40')
print(f"Sig pos: {hex(sig_pos) if sig_pos != -1 else 'Not found'}")
if sig_pos != -1:
    vc, vo, to, w3, w4 = struct.unpack_from('<5H', falc, sig_pos + 4)
    print(f"LOD 0: vc={vc}, vo={hex(vo)}, to={hex(to)}")
    # compare vertices with OBJECTS chunk 3:
    for vi in range(16, 26):
        raw = falc[vo + vi*6 : vo + (vi+1)*6]
        x, y, z = struct.unpack_from('<hhh', raw)
        print(f"FalcObj.Bin v{vi:02d}: x={x:4d}, y={y:4d}, z={z:4d}")
