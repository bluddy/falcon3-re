import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

# Disassemble from 0x2978E to 0x29A00
code = exe[0x2978E:0x29A00]
print("Disassembly from 0x2978E:")
for i in md.disasm(code, 0x2978E):
    print(f"0x{i.address:05x}: {i.mnemonic:8s} {i.op_str}")
    if i.address > 0x29900 and i.mnemonic in ('ret', 'retf'):
        break
