with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Let's search for 0x2978E or the polygon drawer function in FALCONCD.EXE
# In the previous summary, it was noted as:
# 02978e: lodsw; mov cx, ax (vertex count)
# Let's search for lodsw; mov cx, ax: AD 89 C1 or AD 8B C8
pattern1 = bytes([0xad, 0x89, 0xc1])
pattern2 = bytes([0xad, 0x8b, 0xc8])

for p, name in [(pattern1, "ad 89 c1"), (pattern2, "ad 8b c8")]:
    pos = 0
    while True:
        idx = exe.find(p, pos)
        if idx == -1: break
        print(f"Found {name} at {idx:#x}: context: {' '.join(f'{b:02x}' for b in exe[idx:idx+24])}")
        pos = idx + 1
