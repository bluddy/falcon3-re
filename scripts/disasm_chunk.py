import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Header size is 0x2c00. Let's see what segment this corresponds to.
# In IDA: 0x26B2E was likely CS:0x26B2E or linear address.
# Let's disassemble 16-bit x86 around 0x19780 to 0x19850.
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

chunk = exe[0x19780:0x19850]
base_addr = 0x19780
for ins in md.disasm(chunk, base_addr):
    print(f"{ins.address:#06x}:  {ins.mnemonic:10s} {ins.op_str}")
