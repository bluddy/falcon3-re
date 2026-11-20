
import idaapi, idc, idautils

idaapi.auto_wait()

with open('xrefs_441e.txt', 'w') as f:
    for ea in range(0x1F6C0, 0x2AA30):
        if idc.get_wide_word(ea) == 0x441E:
            func = idc.get_func_name(ea)
            dis = idc.generate_disasm_line(ea, 0)
            f.write(f'0x{ea:X} in {func}: {dis}\n')

idc.qexit(0)
