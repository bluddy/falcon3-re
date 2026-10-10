from pathlib import Path
import struct

d = Path('game/FALCONCD.EXE').read_bytes()
tail = 0x1fb51
t = d[tail:]

base = 0x2c00 + 0x1AA3 * 16 + 0x0C1F
recs = []
for i in range(100):
    o = base + i * 18
    if o + 18 > len(d):
        break
    w = struct.unpack_from('<9H', d, o)
    if not (0x100 <= w[0] <= 0x9000):
        break
    recs.append(dict(id=w[7], seg=w[0], off=w[2], A=w[4], B=w[5], C=w[6]))

sorted_recs = sorted([r for r in recs if r['A'] > 0], key=lambda x: x['off'])

# Focus on id7 - the big one with high validity
r7 = next(r for r in sorted_recs if r['id'] == 7)
off, A, B = r7['off'], r7['A'], r7['B']
code_size = A - B
fixup_off = r7['off'] + r7['A'] - r7['B']
fixup_data = t[fixup_off:fixup_off + r7['B']]

print(f"id7: off={off:05x} A={A} B={B} code_size={code_size} fixup_off={fixup_off:05x}")

# Parse as 4-byte entries starting from beginning
print("\n=== First 64 entries (4-byte aligned) ===")
for i in range(0, min(len(fixup_data), 256), 4):
    if i + 3 >= len(fixup_data):
        break
    typ = struct.unpack_from('<H', fixup_data, i)[0]
    offset = struct.unpack_from('<H', fixup_data, i + 2)[0]
    if offset < 12544:  # code_size
        print(f"  [{i//4:3d}] type=0x{typ:04x} offset=0x{offset:04x}")

# Also try with 1-byte offset
print("\n=== Trying 3-byte entries (type:byte, offset:word) ===")
for i in range(0, min(len(fixup_data), 192), 3):
    if i + 2 >= len(fixup_data):
        break
    typ = fixup_bytes[i]
    offset = struct.unpack_from('<H', fixup_bytes, i + 1)[0]
    if offset < 12544:
        print(f"  [{i//3:3d}] type=0x{typ:02x} offset=0x{offset:04x}")

# Try 5-byte entries (type:word, offset:dword)
print("\n=== Trying 6-byte entries (type:word, offset:dword) ===")
for i in range(0, min(len(fixup_data), 256), 6):
    if i + 5 >= len(fixup_data):
        break
    typ = struct.unpack_from('<H', fixup_bytes, i)[0]
    offset = struct.unpack_from('<I', fixup_bytes, i + 2)[0]
    if offset < 12544:
        print(f"  [{i//6:3d}] type=0x{typ:04x} offset=0x{offset:08x}")

# Check if there's a header
print("\n=== First 32 bytes raw ===")
fixup_bytes = fixup_data
print(f"  {fixup_bytes[:32].hex(' ')}")
print(f"  {fixup_bytes[32:64].hex(' ')}")
print(f"  {fixup_bytes[64:96].hex(' ')}")
print(f"  {fixup_bytes[96:128].hex(' ')}")