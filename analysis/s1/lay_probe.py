import idc, idaapi, ida_funcs, ida_bytes, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\lay_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
a = 0x1069A8
while a < 0x1069D8:
    h = ida_bytes.get_item_head(a); fl = ida_bytes.get_flags(h)
    P("%X sz%-2d %-6s %-30s refs->%s" % (h, ida_bytes.get_item_size(h), "code" if ida_bytes.is_code(fl) else "data", idc.generate_disasm_line(h, 0)[:30], [(hex(r.to), r.type) for r in idautils.XrefsFrom(h, 0)]))
    a = h + max(ida_bytes.get_item_size(h), 1)
P("bytes 1069B4..1069D0:", " ".join("%02X" % ida_bytes.get_byte(x) for x in range(0x1069B4, 0x1069D0)))
P("func containing 1069B4:", ida_funcs.get_func(0x1069B4) and hex(ida_funcs.get_func(0x1069B4).start_ea))
out.close(); idc.qexit(0)
