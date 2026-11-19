with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

pattern = bytes([0x8b, 0x3c, 0x83, 0xff, 0xff])
pos = 0
while True:
    idx = exe.find(pattern, pos)
    if idx == -1:
        break
    print(f"Found pattern at exe offset: {idx:#x}")
    print("Bytes:", ' '.join(f'{b:02x}' for b in exe[idx:idx+32]))
    pos = idx + 1
