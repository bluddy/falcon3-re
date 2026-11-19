import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# CS is 0x1000 or similar.
# Target is 0x174d1 in file offset.
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

code = exe[0x174d1:0x174d1 + 100]
print("Disassembly of fixed_vec3_transform at 0x174d1:")
for i in md.disasm(code, 0x174d1):
    print(f"0x{i.address:05x}: {i.mnemonic} {i.op_str}")
    if i.mnemonic in ('ret', 'retf'):
        break
