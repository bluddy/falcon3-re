import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

chunk = exe[0x1c38e:0x1c440]
base_addr = 0x1c38e
for ins in md.disasm(chunk, base_addr):
    print(f"{ins.address:#06x}:  {ins.mnemonic:10s} {ins.op_str}")
