with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

import struct

for addr in [0x51fc6, 0x51fda, 0x51fee, 0x52002]:
    chunk = exe[addr:addr+20]
    words = [f'{w:04x}' for w in struct.unpack('<10H', chunk)]
    print(f"{addr:#06x}: {' '.join(words)}")
