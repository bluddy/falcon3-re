with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Search for calls or jumps to 0x1972e
pattern = bytes([0x1972e & 0xff, (0x1972e >> 8) & 0xff])
pos = 0
while True:
    idx = exe.find(b'\xe8', pos) # relative call
    if idx == -1:
        break
    rel = int.from_bytes(exe[idx+1:idx+3], 'little', signed=True)
    if idx + 3 + rel == 0x1972e:
        print(f"Relative call to 0x1972e found at {idx:#x}")
    pos = idx + 1

# Also search for far calls (9A offset segment) or indirect calls
pos = 0
while True:
    idx = exe.find(b'\x9a\x2e\x97', pos)
    if idx != -1:
        print(f"Far call to 0x1972e found at {idx:#x}")
        pos = idx + 1
    else:
        break
