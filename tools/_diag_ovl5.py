import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils, json, os, sys
log = []
s, e = 0x6CD90, 0x6CDA8
# dump item structure across the span
for a in range(s, e):
    fl = ida_bytes.get_flags(a)
    h = ida_bytes.get_item_head(a)
    is_head = ida_bytes.is_head(fl)
    is_code = ida_bytes.is_code(fl)
    is_data = ida_bytes.is_data(fl)
    if is_head or a == s:
        k = ida_ua.decode_insn(ida_ua.insn_t(), a) if is_code or a==s else 0
        mn = idc.print_insn_mnem(a) if (is_code or a==s) else ''
        log.append("0x%X head=%s code=%s data=%s head_at=0x%X size=%d k=%d mn=%s byte=0x%02X" % (
            a, is_head, is_code, is_data, h, ida_bytes.get_item_size(h), k, mn, ida_bytes.get_byte(a)))
# specifically 0x6CD93
a=0x6CD93
fl=ida_bytes.get_flags(a)
log.append("---")
log.append("0x%X flags=0x%X head=%s code=%s data=%s head_at=0x%X size=%d" % (
    a, fl, ida_bytes.is_head(fl), ida_bytes.is_code(fl), ida_bytes.is_data(fl), ida_bytes.get_item_head(a), ida_bytes.get_item_size(ida_bytes.get_item_head(a))))
log.append("  decode@0x%X -> k=%d" % (a, ida_ua.decode_insn(ida_ua.insn_t(), a)))
# is 0x6CD93 inside the item starting at 0x6CD91 (the or k=2)?
log.append("  item head of 0x6CD91: 0x%X" % ida_bytes.get_item_head(0x6CD91))
with open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\diag_ovl.log", "w") as f:
    f.write("\n".join(log))
idaapi.qexit(0)