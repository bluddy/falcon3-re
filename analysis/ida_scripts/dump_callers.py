import idaapi
import idc

idaapi.auto_wait()

with open("analysis/ida_scripts/callers_disasm.txt", "w") as f:
    for caller in [0x26442, 0x26C71, 0x2717A]:
        f.write(f"\n=== Caller around 0x{caller:X} ===\n")
        start = caller - 0x30
        end = caller + 0x10
        cur = start
        while cur < end:
            dis = idc.generate_disasm_line(cur, 0)
            cmt = idc.get_cmt(cur, 0) or ''
            f.write(f"0x{cur:08X}: {dis:45s} ; {cmt}\n")
            cur = idc.next_head(cur, end)

idc.qexit(0)
