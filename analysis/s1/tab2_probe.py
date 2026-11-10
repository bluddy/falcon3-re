import idc, idaapi, ida_funcs, ida_bytes, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\tab2_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
def dump(lo, hi):
    a = lo
    while a < hi:
        h = ida_bytes.get_item_head(a); f = ida_funcs.get_func(h)
        P("%X %-7s %-36s %s" % (h, "%X" % f.start_ea if f else "-", idc.generate_disasm_line(h, 0)[:36], " ".join("%02X" % ida_bytes.get_byte(h+i) for i in range(min(ida_bytes.get_item_size(h), 6)))))
        a = h + max(ida_bytes.get_item_size(h), 1)
for lo, hi in [(0x106A3A, 0x106A56), (0x106A74, 0x106A84), (0x1069A8, 0x1069BC)]:
    P("====="); dump(lo, hi)
for ea in (0x105D9D, 0x105DA7):
    f = ida_funcs.get_func(ea); P(hex(ea), hex(f.start_ea), hex(f.end_ea), idc.get_func_name(ea))
P("callers of 105D9D:", [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x105D9D, 0)])
P("funcs 105D00..105F00:", [(hex(f), hex(ida_funcs.get_func(f).end_ea), idc.get_func_name(f)) for f in idautils.Functions(0x105D00, 0x105F00)])
out.close(); idc.qexit(0)
