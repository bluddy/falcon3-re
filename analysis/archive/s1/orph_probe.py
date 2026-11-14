import idc, idaapi, ida_funcs, ida_bytes, idautils, ida_ua
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\orph_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
def dump(lo, hi):
    a = lo
    while a < hi:
        h = ida_bytes.get_item_head(a)
        f = ida_funcs.get_func(h)
        P("%X %-8s %-40s %s" % (h, "%X" % f.start_ea if f else "-", idc.generate_disasm_line(h, 0), " ".join("%02X" % ida_bytes.get_byte(h+i) for i in range(min(ida_bytes.get_item_size(h), 8)))))
        a = h + max(ida_bytes.get_item_size(h), 1)
def xr(ea):
    P("  xrefs to %X:" % ea, [(hex(r.frm), r.type) for r in idautils.XrefsTo(ea, 0)])
for name, lo, hi in [("12C4F2", 0x12C4D0, 0x12C520), ("12C9D0", 0x12C9C0, 0x12CA10), ("12CB27", 0x12CB10, 0x12CB40), ("105DA9", 0x105D90, 0x105DD0)]:
    P("=====", name); dump(lo, hi)
for ea in (0x12C4F2, 0x12C9D0, 0x12CB27, 0x105DA9): xr(ea)
for ea in (0x12C4F2, 0x12C9D0, 0x12CB27, 0x105DA7):
    f = ida_funcs.get_func(ea); P(hex(ea), f and (hex(f.start_ea), hex(f.end_ea), idc.get_func_name(f.start_ea)))
P("105DA9..105EB5 funcs:", sorted({hex(ida_funcs.get_func(a).start_ea) for a in range(0x105DA9, 0x105EB5) if ida_funcs.get_func(a)}))
P("bytes 105DA7:", " ".join("%02X" % ida_bytes.get_byte(0x105DA7+i) for i in range(0x20)))
P("bytes 105EA0:", " ".join("%02X" % ida_bytes.get_byte(0x105EA0+i) for i in range(0x30)))
out.close()
idc.qexit(0)
