with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

import struct

table_words = struct.unpack('<20H', exe[0x75c0:0x75c0+40])
print("Table at 0x75c0:")
for i, w in enumerate(table_words):
    print(f"  [{i:2d}] {0x75c0 + i*2:#06x}: {w:#06x}")
