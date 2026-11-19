with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

import re
for m in re.finditer(b'OBJECTS', exe):
    print(f"Found 'OBJECTS' at {hex(m.start())}")
