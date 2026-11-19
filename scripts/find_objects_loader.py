with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Header size is 0x2c00. Let's find references to the string OBJECTS (relative or offset in DS)
# In IDA / real mode, let's search for offset 0x26ac0 - 0x2c00 or search for word 0x3ec0 or similar
for idx in range(len(exe)-2):
    # check if word at idx matches 0x6ac0, 0x4ec0, 0x3ec0, etc.
    w = int.from_bytes(exe[idx:idx+2], 'little')
    if w in [0x6ac0, 0x26ac0 & 0xffff, (0x26ac0 - 0x2c00) & 0xffff]:
        ctx = ' '.join(f'{b:02x}' for b in exe[idx-2:idx+6])
        print(f"Match at {idx:#x}: word={w:#06x}, context: {ctx}")
