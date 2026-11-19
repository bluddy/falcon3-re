import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

print("Function at 0x14ab0:")
chunk = exe[0x14ab0:0x14b00]
for ins in md.disasm(chunk, 0x14ab0):
    print(f"{ins.address:#06x}:  {ins.mnemonic:10s} {ins.op_str}")

print("\nFunction at 0x2321b:")
chunk2 = exe[0x2321b:0x23260]
for ins in md.disasm(chunk2, 0x2321b):
    print(f"{ins.address:#06x}:  {ins.mnemonic:10s} {ins.op_str}")
