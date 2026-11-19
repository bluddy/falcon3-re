import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

chunk = exe[0x26a80:0x26b00]
print("Bytes around 0x26ac0:")
for i in range(0, len(chunk), 16):
    sub = chunk[i:i+16]
    print(f"{0x26a80+i:#06x}: {' '.join(f'{b:02x}' for b in sub)}  |  {sub}")
