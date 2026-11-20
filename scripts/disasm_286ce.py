import idc
cur = 0x0298d9
target = idc.get_operand_value(cur, 0)
print(f'target: 0x{target:x}')
lines = [f'object_3d_record_span_mask_rebuild at 0x{target:x}:']
for _ in range(40):
    lines.append(f'0x{target:06x}: {idc.generate_disasm_line(target, 0)}')
    target = idc.next_head(target)

with open('analysis/span_mask_rebuild.txt', 'w') as out:
    out.write('\n'.join(lines))

idc.qexit(0)
