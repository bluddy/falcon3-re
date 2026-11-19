import struct

with open('game/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

# Let's find call at 0x26B64
# In IDA / disassembler, offset 0x26B64:
# Search for bytes around 26B60:
# 20: push cx (51)
# 21: push cx (51)
# 22: call fixed_vec3_transform_es (E8 xx xx)
# 23: mov word ptr es:[di+2], 0 (26 C7 45 02 00 00)
# 24: add di, 6 (83 C7 06)
# 25: pop cx (59)
# 26: loop (E2 F0)

needle = bytes([0x51, 0x51, 0xE8])
pos = 0
found = []
while True:
    p = exe.find(needle, pos)
    if p == -1:
        break
    if exe[p+5:p+11] == bytes([0x26, 0xC7, 0x45, 0x02, 0x00, 0x00]):
        found.append(p)
    pos = p + 1

print(f"Found matches: {[hex(x) for x in found]}")
if found:
    p = found[0]
    # target of E8 xx xx
    rel_call = struct.unpack_from('<h', exe, p+3)[0]
    target = p + 5 + rel_call
    print(f"Call target: {hex(target)}")
