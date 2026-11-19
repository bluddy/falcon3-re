import idaapi
import idc

idaapi.auto_wait()

with open("analysis/ida_scripts/span_mask_rebuild.txt", "w") as f:
    target = idc.get_name_ea_simple("record_span_mask_rebuild")
    if target == idc.BADADDR:
        # get operand of call at 0x298D9
        target = idc.get_operand_value(0x298D9, 0)
    f.write(f"Function record_span_mask_rebuild at 0x{target:08X}\n")
    cur = target
    end = target + 0x100
    while cur < end:
        dis = idc.generate_disasm_line(cur, 0)
        cmt = idc.get_cmt(cur, 0) or ''
        f.write(f"0x{cur:08X}: {dis:45s} ; {cmt}\n")
        if 'ret' in dis or 'retf' in dis:
            break
        cur = idc.next_head(cur, end)

idc.qexit(0)
