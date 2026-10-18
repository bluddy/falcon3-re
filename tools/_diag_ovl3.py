import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os, sys
log = []
ea, e = 0x6CD90, 0x6CDA8   # manifest span
insn = ida_ua.insn_t()
k = ida_ua.decode_insn(insn, ea)
log.append("entry 0x%X decode k=%d mnem=%s (expect span to 0x%X)" % (ea, k, idc.print_insn_mnem(ea), e))
# build body: create insns from ea to e where no item exists
cur = ea
created = 0
while cur < e:
    if ida_bytes.is_code(ida_bytes.get_flags(cur)) and ida_bytes.is_head(ida_bytes.get_flags(cur)):
        # existing code item -- step over it
        sz = ida_bytes.get_item_size(cur)
        cur += sz
        continue
    i2 = ida_ua.insn_t()
    kk = ida_ua.decode_insn(i2, cur)
    if kk <= 0:
        log.append("  decode fail @0x%X" % cur)
        break
    # clear any blocking head inside this insn
    blocking = []
    for pos in range(cur+1, min(cur+kk, e)):
        hh = ida_bytes.get_item_head(pos)
        if hh != cur and ida_bytes.is_head(ida_bytes.get_flags(hh)):
            blocking.append(hh)
    for hh in blocking:
        ida_bytes.del_items(hh, ida_bytes.DELIT_SIMPLE, max(ida_bytes.get_item_size(hh),1))
    if not ida_bytes.is_code(ida_bytes.get_flags(cur)):
        ida_ua.create_insn(cur)
        created += 1
    cur += kk
log.append("built body: %d insns created, cur=0x%X" % (created, cur))
# now add_func with explicit end
ok = ida_funcs.add_func(ea, e)
log.append("add_func(0x%X, 0x%X) -> %s" % (ea, e, ok))
if ok:
    f = ida_funcs.get_func(ea)
    log.append("  span 0x%X..0x%X (want 0x%X..0x%X)" % (f.start_ea, f.end_ea, ea, e))
    ida_funcs.del_func(ea)
else:
    # why? check if any item blocks the end
    log.append("  get_func after fail: %s" % (ida_funcs.get_func(ea),))
    # check last byte of span
    log.append("  flags @0x%X = 0x%X is_code=%s" % (e-1, ida_bytes.get_flags(e-1), ida_bytes.is_code(ida_bytes.get_flags(e-1))))
with open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\diag_ovl.log", "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)