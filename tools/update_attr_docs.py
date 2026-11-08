#!/usr/bin/env python3
import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Update structures.md
t = open('docs/structures.md', 'r', encoding='utf-8').read()
old = '+20 u16 attr         ; 0x14 always; also 0x32 (HOK/IRQ/ISR/PAN), 0x64 (BOS/HOK/KOR), 0xC8 (BOS/HOK) — semantics unknown'
new = '+20 u16 attr         ; coordinate scale factor (0x14=base coastline, 0x32=river, 0x64=lake, 0xC8=border); read by pos_diff_norm (0x28874), shifted by attr_scale_shift (word_1F6E6), used as divisor in fixed-point division for X/Y/Z deltas (finding 107)'
t = t.replace(old, new)
open('docs/structures.md', 'w', encoding='utf-8', newline='').write(t)
print('structures.md updated')

# Update structs.yaml
t = open('registry/structs.yaml', 'r', encoding='utf-8').read()
old = '- {offset: 0x20, size: 2, name: attr,        type: uint16, comment: "0x14 always; 0x32/0x64/0xC8 also seen; semantics unknown"}'
new = '- {offset: 0x20, size: 2, name: attr,        type: uint16, comment: "coordinate scale factor: 0x14=base coastline, 0x32=river, 0x64=lake, 0xC8=border; read by pos_diff_norm (shifted by attr_scale_shift, used as divisor for X/Y/Z deltas)"}'
t = t.replace(old, new)
open('registry/structs.yaml', 'w', encoding='utf-8', newline='').write(t)
print('structs.yaml updated')