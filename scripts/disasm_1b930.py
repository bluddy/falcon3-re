import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

chunk = exe[0x1b930:0x1b9a0]
for ins in md.disasm(chunk, 0x1b930):
    print(f"{ins.address:#06x}:  {ins.mnemonic:10s} {ins.op_str}")
