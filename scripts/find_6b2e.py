with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Search for word 0x6b2e
pattern = bytes([0x2e, 0x6b])
pos = 0
while True:
    idx = exe.find(pattern, pos)
    if idx == -1: break
    print(f"Reference to 0x6b2e at file offset {idx:#x}: context: {' '.join(f'{b:02x}' for b in exe[idx-4:idx+8])}")
    pos = idx + 1
