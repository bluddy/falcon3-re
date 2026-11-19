import capstone

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

# In the binary, the call at 0x197a0 was: call 0x1293b
# Notice: E8 xx xx is a relative call!
# Let's inspect the actual bytes at 0x197a0:
rel_bytes = exe[0x197a0:0x197a3]
rel_off = int.from_bytes(rel_bytes[1:3], 'little', signed=True)
target = 0x197a3 + rel_off
print(f"Call at 0x197a0 is relative offset {rel_off:#x} -> target exe offset {target:#x}")

chunk = exe[target:target+64]
for ins in md.disasm(chunk, target):
    print(f"{ins.address:#06x}:  {ins.mnemonic:10s} {ins.op_str}")
