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

# Deep dive into id7 fixup table (the large one with 48.9% validity)
r7 = next(r for r in sorted_recs if r['id'] == 7)
off, A, B = r7['off'], r7['A'], r7['B']
code_size = A - B
fixup_off = r7['off'] + r7['A'] - r7['B']
fixup_data = t[fixup_off:fixup_off + r7['B']]

print(f"id7 fixup table: {len(fixup_data)} bytes at tail+{fixup_off:05x}")
print(f"Code size: {code_size}, Fixup table size: {r7['B']}")

# Parse as bytes and look for structure
fixup_bytes = fixup_data

# Try different interpretations:
# 1. Byte pairs: (type, offset)
print("\n=== Byte pairs (type, offset) ===")
for i in range(0, min(len(fixup_bytes)-1, 64), 2):
    typ = fixup_bytes[i]
    off_val = fixup_bytes[i+1] if i+1 < len(fixup_bytes) else 0
    if typ != 0 or off_val != 0:
        print(f"  [{i//2:3d}] type={typ:02x} off={off_val:02x}")

# 2. Word pairs: (type, offset) as words
print("\n=== Word pairs (type, offset) as words ===")
words = struct.unpack(f'<{len(fixup_bytes)//2}H', fixup_bytes[:len(fixup_bytes)-len(fixup_bytes)%2])
for i in range(0, min(len(words)-1, 64), 2):
    typ = words[i]
    off_val = words[i+1]
    if typ != 0 or off_val != 0:
        print(f"  [{i//2:3d}] type={typ:04x} off={off_val:04x}")

# 3. Try: first byte is count, then entries
print("\n=== First byte as count ===")
if len(fixup_bytes) > 0:
    count = fixup_bytes[0]
    print(f"  Count byte: {count}")
    # Try parsing count entries of 3 bytes each (type + offset word)
    for i in range(count):
        off = 1 + i * 3
        if off + 2 < len(fixup_bytes):
            typ = fixup_bytes[off]
            off_val = struct.unpack('<H', fixup_bytes[off+1:off+3])[0]
            print(f"  [{i:3d}] type={typ:02x} off={off_val:04x}")

# 3b. Try 4-byte entries: type byte + 3-byte offset? or type word + offset word?
print("\n=== 4-byte entries (type word + offset word) ===")
for i in range(0, min(len(fixup_bytes)-3, 64), 4):
    typ = struct.unpack('<H', fixup_bytes[i:i+2])[0]
    off_val = struct.unpack('<H', fixup_bytes[i+2:i+4])[0]
    if typ != 0 or off_val != 0:
        print(f"  [{i//4:3d}] type={typ:04x} off={off_val:04x}")

# Check if fixup entries are relative to segment base
print("\n=== Checking valid fixups as segment:offset ===")
# The valid fixups from earlier were at odd indices with values like 2522, 1f74, etc.
# Let's see if they're segment:offset pairs
valid_words = [3, 5, 9, 15, 19, 21, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47]
print("Valid indices (from earlier):", valid_words[:20])
# These are word indices in the fixup table
# If entries are 2 words each (type, offset), then entry n is at words[2n], words[2n+1]
# The valid indices were 3,5,9,15,19,21,29,31,33,35,37,39,41,43,45,47
# These are word indices. If entries are 2 words, entry n is at 2n, 2n+1
# So valid entry indices would be 1, 2, 4, 7, 9, 10, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23
# That's not a clear pattern either.

# Let's look at the raw bytes around the valid fixups
fixup_bytes = t[r7['off']+r7['A']-r7['B']:r7['off']+r7['A']]
print(f"\nFixup table bytes (first 128): {fixup_bytes[:128].hex(' ')}")
print(f"Fixup table bytes (next 128): {fixup_bytes[128:256].hex(' ')}")