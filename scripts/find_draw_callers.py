with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Let's find callers of 0x26B2E
# 0x26B2E is a FAR function (it ends with retf at 0x26C21).
# In 16-bit x86, far calls are:
# 9A off_lo off_hi seg_lo seg_hi
# Or through function pointers.
# Let's find all far calls or near calls to 26B2E or 0x6B2E:

# In seg020, base is 0x1F6C0 (file offset around 0x1F8C0).
# Let's search for 0x6B2E:
needle = (0x6B2E).to_bytes(2, 'little')
pos = 0
found = []
while True:
    p = exe.find(needle, pos)
    if p == -1:
        break
    found.append(p)
    pos = p + 1

print(f"Occurrences of 0x6B2E: {[hex(p) for p in found]}")
for p in found:
    print(f"Context at {hex(p)}: {' '.join(f'{b:02x}' for b in exe[p-2:p+6])}")
