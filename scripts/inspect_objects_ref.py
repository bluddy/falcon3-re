import capstone
import struct

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Let's search for references to offset around 0x26ac0
# In 16-bit DOS exe, data offsets are typically DS-relative.
# Let's see what is around 0x26ac0 in the binary:
print("Context around 0x26ac0:")
print(exe[0x26aa0:0x26b00])
