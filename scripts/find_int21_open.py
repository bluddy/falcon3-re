import struct
import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Search for the string "OBJECTS"
pos = exe.find(b'OBJECTS\x00')
print(f"String 'OBJECTS' at file offset: {hex(pos)}")

# In DOS, let's find DOS interrupts (int 21h, ax=3d00h to open file)
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

# Search for int 21h (CD 21)
int21s = []
p = 0
while True:
    p = exe.find(b'\xcd\x21', p)
    if p == -1:
        break
    # check instructions before
    int21s.append(p)
    p += 1

print(f"Found {len(int21s)} int 21h calls")

# Look for open file calls (mov ah, 3dh or mov ax, 3d00h) near int 21h
open_calls = []
for ip in int21s:
    # disassemble 30 bytes before ip
    start = max(0, ip - 30)
    code = exe[start:ip+2]
    for instr in md.disasm(code, start):
        if instr.mnemonic == 'mov' and ('3d' in instr.op_str):
            open_calls.append(ip)
            break

print(f"Found {len(open_calls)} open calls (int 21h ah=3dh)")
for oc in open_calls:
    print(f"Open at file offset {hex(oc)}")
