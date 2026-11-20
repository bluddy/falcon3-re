
import idaapi, idc, idautils

idaapi.auto_wait()

with open('table_27974.txt', 'w') as f:
    for i in range(8):
        ea = 0x27974 + i * 2
        tgt = idc.get_wide_word(ea)
        name = idc.get_name(tgt)
        f.write(f'off_27974[{i*2}]: 0x{tgt:04X} ({name})\n')

idc.qexit(0)
