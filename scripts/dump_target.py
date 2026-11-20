import idc
import idaapi

idaapi.auto_wait()

b = [idc.get_wide_byte(0x26B64 + i) for i in range(5)]
print("Bytes:", [hex(x) for x in b])
# In 16-bit x86, call near is E8 rel16
rel = idc.get_wide_word(0x26B65)
if rel >= 0x8000:
    rel -= 0x10000
next_ip = (0x26B64 + 3) & 0xFFFF
target_ip = (next_ip + rel) & 0xFFFF
seg = 0x26B64 & 0xF0000
target_ea = seg | target_ip
print(f"Target ea: 0x{target_ea:X}, name: {idc.get_name(target_ea)}")

out_lines = []
cur = target_ea
for _ in range(30):
    dis = idc.generate_disasm_line(cur, 0)
    out_lines.append(f"0x{cur:08X}: {dis}")
    cur = idc.next_head(cur)

with open(r'analysis/viewer/disasm_target_26b64.txt', 'w') as f:
    f.write('\n'.join(out_lines))

idc.qexit(0)
