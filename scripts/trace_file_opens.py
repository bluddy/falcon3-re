import capstone
import struct

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Let's check the open calls found earlier:
# Open at file offset 0x31ec
# Open at file offset 0x31f5
# Open at file offset 0x3202
# Open at file offset 0x3486
# Open at file offset 0x3499
# Open at file offset 0x349d
# Open at file offset 0x152bd
# Open at file offset 0x152c5
# Open at file offset 0x1d30f
# Open at file offset 0x1d31d
# Open at file offset 0x1dadc
# Open at file offset 0x1db3a
# Open at file offset 0x1fa05
# Open at file offset 0x1fcd1
# Open at file offset 0x1fcde
# Open at file offset 0x289a9
# Open at file offset 0x289b7

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)

target_offsets = [0x152bd, 0x1d30f, 0x1dadc, 0x1fa05, 0x1fcd1, 0x289a9]

for toff in target_offsets:
    print(f"\n=== Code before 0x{toff:X} ===")
    code = exe[toff - 40 : toff + 20]
    for instr in md.disasm(code, toff - 40):
        print(f"  0x{instr.address:05x}: {instr.mnemonic:8s} {instr.op_str}")
