import struct
from pathlib import Path

# Let's inspect MAPOBJ.ISR
data = Path('game/MAPOBJ.ISR').read_bytes()
print(f"MAPOBJ.ISR size: {len(data)} bytes")

# Read header offsets at 0x48..0xC0
offsets = []
for i in range(0x48, 0xC0, 4):
    off = struct.unpack_from('<I', data, i)[0]
    if off != 0xFFFFFFFF and off < len(data):
        offsets.append((i, off))

print("Valid section offsets in MAPOBJ.ISR:")
for hdr_off, sec_off in offsets:
    print(f"  hdr 0x{hdr_off:02X} -> offset 0x{sec_off:06X} ({sec_off})")

# Let's see what is at offset 0x100..0x7000 and beyond 0x7000
for hdr_off, sec_off in offsets:
    sample = [struct.unpack_from('<i', data, sec_off + 4*k)[0] for k in range(min(8, (len(data)-sec_off)//4))]
    print(f"  Section at 0x{sec_off:06X}: {[hex(s & 0xFFFFFFFF) for s in sample]}")
