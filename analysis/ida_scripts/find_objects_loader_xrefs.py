import idaapi
import idc
import idautils

idaapi.auto_wait()

with open("analysis/ida_scripts/objects_loader_xref.txt", "w") as f:
    # search for bytes "OBJECTS" in binary
    ea = idaapi.get_imagebase()
    # Find all occurrences of "OBJECTS"
    pos = 0
    while True:
        target = idc.find_binary(pos, idc.SEARCH_DOWN, '"OBJECTS"')
        if target == idc.BADADDR:
            break
        f.write(f"String 'OBJECTS' at 0x{target:X}\n")
        for xref in idautils.XrefsTo(target):
            f.write(f"  Xref from 0x{xref.frm:X} (type {xref.type})\n")
            # disassemble 40 instructions around xref.frm
            func = idaapi.get_func(xref.frm)
            if func:
                f.write(f"  In function 0x{func.start_ea:X} - 0x{func.end_ea:X}\n")
                cur = func.start_ea
                while cur < func.end_ea:
                    dis = idc.generate_disasm_line(cur, 0)
                    f.write(f"    0x{cur:08X}: {dis}\n")
                    cur = idc.next_head(cur, func.end_ea)
        pos = target + 1

idc.qexit(0)
