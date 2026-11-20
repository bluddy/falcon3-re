import idaapi
import idc

idaapi.auto_wait()

with open("analysis/ida_scripts/disasm_26b7b.txt", "w") as f:
    target = idc.get_operand_value(0x26B7B, 0)
    name = idc.get_func_name(target)
    f.write(f"Function at 0x{target:X} ({name}):\n")
    cur = target
    end = target + 0x200
    while cur < end:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ''
        f.write(f"0x{cur:08X}: {dis:45s} ; {cmt}\n")
        if 'ret' in dis or 'retf' in dis:
            break
        cur = idc.next_head(cur, end)

idc.qexit(0)
