import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os
ROOT = r"C:\Users\yotam\projects\falcon3"
log = []
# sub_1018F, sub_22AFF: are they ISR/vector/callback?  Check what calls them dynamically
# by looking at their entry context + whether they're in an interrupt vector.
for ea in (0x1018F, 0x22AFF):
    fn = ida_funcs.get_func(ea)
    log.append("=== ea=0x%X name=%s size=%d ===" % (ea, idc.get_func_name(ea),
               (fn.end_ea-fn.start_ea) if fn else -1))
    # who references it as data (vector table / pointer)?
    drefsto = [hex(x) for x in idautils.DataRefsTo(ea)]
    crefsto = [hex(x) for x in idautils.CodeRefsTo(ea, 0)]
    log.append("  CodeRefsTo: %s" % crefsto)
    log.append("  DataRefsTo: %s (pointer/vector refs)" % drefsto)
    # is it referenced by a far-call immediate (E8/E9 with seg)?
    # check segment
    seg = idaapi.getseg(ea)
    log.append("  seg: %s [0x%X..0x%X]" % (idc.get_segm_name(ea) if seg else "?",
               seg.start_ea, seg.end_ea) if seg else "  no seg")
    # decode first few insns
    cur = ea
    for _ in range(6):
        insn = ida_ua.insn_t()
        k = ida_ua.decode_insn(insn, cur)
        if k <= 0: break
        log.append("  0x%X: %s %s" % (cur, idc.print_insn_mnem(cur),
                   " ".join(idc.print_operand(cur,i) for i in range(2))))
        cur += k
    log.append("")

# DATA-class leaves: full range + does it fall through?
for ea in (0x22C91, 0x22C62):
    fn = ida_funcs.get_func(ea)
    sz = (fn.end_ea - fn.start_ea) if fn else 0
    end = ea + sz
    log.append("=== DATA ea=0x%X size=%d ===" % (ea, sz))
    # what's immediately after?
    nxt = ida_funcs.get_func(end)
    log.append("  ends at 0x%X; next func: %s (start 0x%X)" % (
        end, idc.get_func_name(end) if nxt else "NONE",
        nxt.start_ea if nxt else 0))
    # decode the whole thing as code -- does it terminate?
    cur = ea
    term = None
    for _ in range(64):
        insn = ida_ua.insn_t()
        k = ida_ua.decode_insn(insn, cur)
        if k <= 0:
            log.append("  decode fail at 0x%X (byte=0x%02X)" % (cur, ida_bytes.get_byte(cur)))
            break
        mn = idc.print_insn_mnem(cur).lower()
        if mn in ("retn","retf","ret","iret","jmp"):
            term = mn
            log.append("  TERMINATOR %s at 0x%X (fn ends 0x%X)" % (mn, cur, end))
            break
        cur += k
    if term is None:
        log.append("  NO terminator in window; last decoded 0x%X; fn end 0x%X" % (cur, end))
    # class was DATA -- why? check flags
    log.append("  is_data(ea)=%s is_code(ea)=%s" % (
        ida_bytes.is_data(ida_bytes.get_flags(ea)),
        ida_bytes.is_code(ida_bytes.get_flags(ea))))
    # first insn
    insn = ida_ua.insn_t()
    k = ida_ua.decode_insn(insn, ea)
    log.append("  first decode k=%d mn=%s" % (k, idc.print_insn_mnem(ea)))
    log.append("")

with open(os.path.join(ROOT, "analysis/ida_falconcd/diag_leaves.log"), "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)