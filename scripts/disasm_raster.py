import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

chunk = exe[0x1c4c0:0x1c540]
for ins in md.disasm(chunk, 0x1c4c0):
    print(f"{ins.address:#06x}:  {ins.mnemonic:10s} {ins.op_str}")
