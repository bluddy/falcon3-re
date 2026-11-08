import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
with open('docs/findings_log.md', 'a', encoding='utf-8') as f:
    f.write('''

## 2026-10-24 109 - ISLDAT sub-record flags: 0x1000 = node chain flag

Status: CONFIRMED (validated in pos_diff_norm disasm)

**Discovery**: In pos_diff_norm (0x28874), the sub-record flags field (+0x00) is tested:

```
0x28A5C: lodsw          ; load flags from sub-record +0x00
0x28A5F: and   bx, 1000h  ; test bit 0x1000
0x28A63: mov   cs:byte_1F73E, bh  ; store result (0x10 or 0x00)
...
0x28A81: cmp   cs:byte_1F73E, 0
0x28A87: jz     single_node_path   ; flags & 0x1000 == 0
; else: node chain path (FFFF-terminated list)
```

**Semantics**:
- flags & 0x1000 == 1 -> node chain (FFFF-terminated list of line-table offsets)
- flags & 0x1000 == 0 -> single node (exactly one line-table offset, no terminator)

**Correction to Finding 105**: Previously noted "flags & 0x1000 -> chain until FFFF, else exactly one node no terminator" - CONFIRMED correct.

**Flag 0x0002**: Appears in combination (0x1002, 0x0002) in IRQ, ISR, PAN, HOK, NEL. Not tested in pos_diff_norm node walker. Semantics still OPEN (possibly used in opcode handlers).

**Registry updates**: byte_1F73E (temp flag for 0x1000 test) already in ledger.
''')
print('done')