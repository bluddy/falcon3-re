import idaapi
import idc

idaapi.auto_wait()

# 0x289A9 in file is segment R05_1F64 or seg020?
# In seg020 (base 0x1F6C0):
# 0x289A9 - 0x200 = 0x287A9?
# Let's search in IDA for instructions matching 0x289A9:
pos = 0x10000
found = []
while True:
    ea = idc.find_binary(pos, idc.SEARCH_DOWN, "B8 00 3D CD 21")
    if ea == idc.BADADDR:
        break
    found.append(ea)
    pos = ea + 1

with open("analysis/ida_scripts/open_3d00.txt", "w") as f:
    f.write(f"Matches for mov ax, 3d00h; int 21h: {[hex(x) for x in found]}\n")
    for ea in found:
        func = idaapi.get_func(ea)
        if func:
            f.write(f"\nFunction at 0x{func.start_ea:X} - 0x{func.end_ea:X} (name {idc.get_func_name(func.start_ea)}):\n")
            cur = func.start_ea
            while cur < min(func.end_ea, func.start_ea + 300):
                dis = idc.generate_disasm_line(cur, 0)
                cmt = idc.get_cmt(cur, 0) or ''
                f.write(f"  0x{cur:08X}: {dis:45s} ; {cmt}\n")
                cur = idc.next_head(cur, func.end_ea)

idc.qexit(0)
