with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

pos = 0
while True:
    idx = exe.find(b'\x1e\x44', pos)
    if idx == -1: break
    ctx = ' '.join(f'{b:02x}' for b in exe[idx-4:idx+8])
    print(f"Reference to 0x441e at exe offset {idx:#x}: {ctx}")
    pos = idx + 1
