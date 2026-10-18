import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os, sys
log = []
ea = 0x6CD90
# decode first insn
insn = ida_ua.insn_t()
k = ida_ua.decode_insn(insn, ea)
log.append("entry 0x%X decode k=%d mnem=%s" % (ea, k, idc.print_insn_mnem(ea)))
# items inside the first insn (blocking)
blocking = []
for pos in range(ea+1, min(ea+k, ea+8)):
    hh = ida_bytes.get_item_head(pos)
    if hh != ea and ida_bytes.is_head(ida_bytes.get_flags(hh)):
        blocking.append(hh)
log.append("blocking heads in first insn: %s" % [hex(x) for x in blocking])
# clear them
for hh in blocking:
    nn = max(ida_bytes.get_item_size(hh), 1)
    ida_bytes.del_items(hh, ida_bytes.DELIT_SIMPLE, nn)
    log.append("cleared %dB @0x%X" % (nn, hh))
# re-decode
k2 = ida_ua.decode_insn(ida_ua.insn_t(), ea)
log.append("re-decode k=%d" % k2)
# is there a function overlapping already?
fn = ida_funcs.get_func(ea)
log.append("get_func=0x%X" % (fn.start_ea if fn else 0))
# try add_func
ok = ida_funcs.add_func(ea)
log.append("add_func(0x%X) -> %s" % (ea, ok))
if ok:
    f2 = ida_funcs.get_func(ea)
    log.append("  created span 0x%X..0x%X" % (f2.start_ea, f2.end_ea))
    ida_funcs.del_func(ea)
# check chunk flags / segment
seg = idaapi.getseg(ea)
log.append("seg perm=0x%X flags=0x%X" % (seg.perm, seg.flags) if seg else "no seg")
# check if this is the start of the segment
log.append("seg.start=0x%X" % (seg.start_ea if seg else 0))
# try add_func with explicit end (decode to a terminator)
cur = ea
term = None
for _ in range(512):
    i2 = ida_ua.insn_t()
    kk = ida_ua.decode_insn(i2, cur)
    if kk <= 0: break
    m = idc.print_insn_mnem(cur).lower()
    if m in ('retn','retf','ret','iret','jmp'):
        term = cur
        kk2 = ida_ua.decode_insn(ida_ua.insn_t(), cur)
        if kk2 > 0: cur += kk2
        break
    cur += kk
if term:
    ok2 = ida_funcs.add_func(ea, cur)
    log.append("add_func(0x%X, 0x%X) -> %s" % (ea, cur, ok2))
    if ok2:
        ida_funcs.del_func(ea)
else:
    log.append("no terminator found in 512 insns")
with open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\diag_ovl.log", "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)