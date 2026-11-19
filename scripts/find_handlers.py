import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Let's find where CS data is located relative to 0x19780.
# In 0x19809: call word ptr cs:[bx - 0x7d4c]
# In 16-bit x86, CS is the code segment.
# In 0x19809, the opcode was: 2e ff 97 a8 6d (Wait, 0x197f5 used [bx + 0x82b4]? No, let's look at 0x19809 bytes)
chunk = exe[0x19808:0x19812]
print('Bytes at 0x19808:', ' '.join(f'{b:02x}' for b in chunk))
