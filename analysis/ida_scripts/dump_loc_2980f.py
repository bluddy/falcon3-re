import idaapi
import idc

idaapi.auto_wait()

with open("analysis/ida_scripts/loc_2980F.txt", "w") as f:
    cur = 0x2980E
    end = 0x298C5
    while cur < end:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ''
        f.write(f"0x{cur:08X}: {dis:45s} ; {cmt}\n")
        cur = idc.next_head(cur, end)

idc.qexit(0)
