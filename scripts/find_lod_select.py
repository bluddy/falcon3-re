# Let's inspect the caller of 0x1972e by checking where cs is set or looking at functions around 0x19000-0x1b000
import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

# In 16-bit real mode code, let's search for references to 0x6b2e or other functions in the same segment
# Let's search for the pattern that sets si to the LOD header:
# In the LOD header: vc, vo, to.
# Let's search for "cmp dx" or distance checks that select the LOD!
# LOD selection typically does:
# if dist < d0: use lod 0
# elif dist < d1: use lod 1
# etc.
print("Searching for LOD selection logic...")
# Let's search for bytes ff ff 00 40 in the exe code that might be searching for the model header
for idx in range(0x2c00, len(exe)-4):
    if exe[idx:idx+4] == b'\xff\xff\x00\x40':
        print(f"Found signature at {idx:#x}")
