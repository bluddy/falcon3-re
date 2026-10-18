import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os, sys
log = []
for ea in (0x6CD90, 0x6CD9F):
    h = ida_bytes.get_item_head(ea)
    fl = ida_bytes.get_flags(ea)
    flh = ida_bytes.get_flags(h)
    insn = ida_ua.insn_t()
    k = ida_ua.decode_insn(insn, ea)
    kh = ida_ua.decode_insn(ida_ua.insn_t(), h)
    fn = ida_funcs.get_func(ea)
    log.append("0x%X: head=0x%X flags=0x%X is_head=%s is_code=%s decode_k=%d mnem=%s | head decode_k=%d mnem=%s | in_fn=%s" % (
        ea, h, fl, ida_bytes.is_head(fl), ida_bytes.is_code(fl),
        k, idc.print_insn_mnem(ea), kh, idc.print_insn_mnem(h),
        fn.start_ea if fn else None))
    # is ea mid-instruction?
    if h < ea:
        log.append("  -> MID-INSTRUCTION (head 0x%X, ea is +%d into it)" % (h, ea-h))
    # try add_func at head
    ok = ida_funcs.add_func(h)
    if ok:
        ida_funcs.del_func(h)
        log.append("  add_func(head 0x%X) -> True" % h)
    else:
        log.append("  add_func(head 0x%X) -> False" % h)
with open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\diag_ovl.log", "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)