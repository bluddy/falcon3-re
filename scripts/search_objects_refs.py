with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Let's search for references to offset 0x26ac0 (the string "OBJECTS")
# In FALCONCD.EXE, offset 0x26ac0.
# Where is 0x26ac0 passed to fopen/open?
# Let's search for bytes: c0 6a (or offset of "OBJECTS")
for idx in range(len(exe)-2):
    w = int.from_bytes(exe[idx:idx+2], 'little')
    # If DS offset of string OBJECTS
    # Let's check what segment 0x26ac0 is in
    pass

# Let's search for "OBJECTS" across all files in game/
import os
for root, dirs, files in os.walk('game'):
    for file in files:
        fp = os.path.join(root, file)
        try:
            with open(fp, 'rb') as f:
                content = f.read()
                if b'OBJECTS' in content and file != 'OBJECTS':
                    print(f"Found 'OBJECTS' in {fp}")
        except Exception:
            pass
