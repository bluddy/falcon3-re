import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os
ROOT = r"C:\Users\yotam\projects\falcon3"
log = []
# sub_22C62: span 0x22C62..0x22C8B, retf at 0x22C70.  What is 0x22C71..0x22C8B?
log.append("=== sub_22C62 (0x22C62..0x22C8B), retf @ 0x22C70 ===")
log.append("bytes 0x22C62..0x22C8A: %s" % (idc.get_bytes(0x22C62, 0x22C8B-0x22C62) or b"").hex())
# decode full span
cur = 0x22C62
while cur < 0x22C8B:
    insn = ida_ua.insn_t()
    k = ida_ua.decode_insn(insn, cur)
    if k <= 0:
        log.append("  0x%X: UNDECODABLE 0x%02X" % (cur, ida_bytes.get_byte(cur)))
        break
    mn = idc.print_insn_mnem(cur)
    ops = " ".join(idc.print_operand(cur,i) for i in range(3) if idc.print_operand(cur,i))
    tag = ""
    if cur == 0x22C70: tag = "  <<< RETF (real end)"
    if cur > 0x22C70: tag = "  <<< AFTER retf"
    log.append("  0x%X: %s %s%s" % (cur, mn, ops, tag))
    cur += k
# what function owns 0x22C71..0x22C8B?
for probe in (0x22C71, 0x22C80, 0x22C8A):
    f = ida_funcs.get_func(probe)
    log.append("  0x%X in fn: %s" % (probe, "%s (0x%X..0x%X)" % (idc.get_func_name(f.start_ea), f.start_ea, f.end_ea) if f else "NONE"))
# next fn after 0x22C8B
nf = ida_funcs.get_func(0x22C8B)
log.append("  fn at/after 0x22C8B: %s" % ("%s (0x%X..0x%X)" % (idc.get_func_name(nf.start_ea), nf.start_ea, nf.end_ea) if nf else "NONE"))
log.append("")
# sub_22C91: span 0x22C91..0x22C9E, real chain to retf @0x22CD4
log.append("=== sub_22C91 (span 0x22C91..0x22C9E), real retf @ 0x22CD4 ===")
log.append("bytes 0x22C91..0x22CD4: %s" % (idc.get_bytes(0x22C91, 0x22CD5-0x22C91) or b"").hex())
cur = 0x22C91
n = 0
while cur <= 0x22CD4:
    insn = ida_ua.insn_t()
    k = ida_ua.decode_insn(insn, cur)
    if k <= 0:
        log.append("  0x%X: UNDECODABLE 0x%02X" % (cur, ida_bytes.get_byte(cur)))
        break
    mn = idc.print_insn_mnem(cur)
    ops = " ".join(idc.print_operand(cur,i) for i in range(3) if idc.print_operand(cur,i))
    tag = ""
    if cur == 0x22C9E: tag = "  <<< current fn END (nullsub_19 here)"
    if cur == 0x22CD4: tag = "  <<< RETF (real end)"
    log.append("  0x%X: %s %s%s" % (cur, mn, ops, tag))
    n += 1
    if mn.lower() in ("retf","retn","ret","iret"): break
    cur += k
# nullsub_19
ns = ida_funcs.get_func(0x22C9E)
log.append("  nullsub_19: %s (0x%X..0x%X) size=%d" % (idc.get_func_name(ns.start_ea) if ns else "?", ns.start_ea if ns else 0, ns.end_ea if ns else 0, (ns.end_ea-ns.start_ea) if ns else 0))
# is there a gap 0x22C9E..0x22CA0 (2B nullsub) then code continues?
log.append("  bytes @0x22C9E..0x22CA1: %s" % (idc.get_bytes(0x22C9E, 3) or b"").hex())
with open(os.path.join(ROOT, "analysis/ida_falconcd/diag_hygiene.log"), "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)