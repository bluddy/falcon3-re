with open('analysis/ida_falconcd/FALCONCD.EXE', 'rb') as f:
    exe = f.read()

with open('memdump/MEMDUMP7_flight_outside_view.BIN', 'rb') as f:
    dump = f.read()

# Let's find 32 consecutive code bytes that have no relocation fixups
# In object_3d_record_span_mask_rebuild (0x299D5 in IDA):
# 0x000299D5: 2E C7 06 ... (wait, CS overrides)
# Let's find the bytes of loc_28D14 (the inner loop of 0x28CA1):
# 51 AD 8B D8 AD 8B E8 AD 8B C8 56 57
pat = bytes.fromhex('51 ad 8b d8 ad 8b e8 ad 8b c8 56 57')
pos_in_exe = exe.find(pat)
pos_in_dump = dump.find(pat)

print(f'Pattern pos in EXE: 0x{pos_in_exe:X}')
print(f'Pattern pos in DUMP: 0x{pos_in_dump:X}')

if pos_in_dump != -1:
    delta = pos_in_dump - pos_in_exe
    print(f'Relocation delta (DUMP - EXE): 0x{delta:X} ({delta} bytes)')
    # In IDA, 0x28D14 was at:
    ida_addr = 0x28D14
    # The actual physical address in dump:
    actual_phys = pos_in_dump
    print(f'Actual physical in DUMP: 0x{actual_phys:X} (seg = 0x{actual_phys//16:04X}, off = 0x{actual_phys%16:04X})')
