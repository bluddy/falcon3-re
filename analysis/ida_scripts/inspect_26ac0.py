import idaapi
import idc
import idautils

idaapi.auto_wait()

ea = 0x26AC0
with open("analysis/ida_scripts/inspect_26ac0.txt", "w") as f:
    f.write(f"Bytes at 0x{ea:X}: {idaapi.get_bytes(ea, 32)}\n")
    for xref in idautils.XrefsTo(ea):
        f.write(f"  Xref from 0x{xref.frm:X} (type {xref.type})\n")
        # disassemble 10 instructions
        cur = xref.frm - 10
        while cur < xref.frm + 20:
            dis = idc.generate_disasm_line(cur, 0)
            f.write(f"    0x{cur:08X}: {dis}\n")
            cur = idc.next_head(cur, xref.frm + 20)

idc.qexit(0)
