import idc, idaapi, ida_funcs, ida_bytes, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\tab_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
def dump(lo, hi):
    a = lo
    while a < hi:
        h = ida_bytes.get_item_head(a); f = ida_funcs.get_func(h)
        P("%X %-7s %-34s %s %s" % (h, "%X" % f.start_ea if f else "-", idc.generate_disasm_line(h, 0)[:34], " ".join("%02X" % ida_bytes.get_byte(h+i) for i in range(min(ida_bytes.get_item_size(h), 6))), idc.get_name(h) if idc.get_name(h) and not idc.get_name(h).startswith(("loc_","sub_")) else ""))
        a = h + max(ida_bytes.get_item_size(h), 1)
def xr(ea): P("  xrefs to %X:" % ea, [(hex(r.frm), r.type) for r in idautils.XrefsTo(ea, 0)])
for name, lo, hi, xs in [("6EC14", 0x6EBF0, 0x6EC60, (0x6EC14,0x6EC17)), ("6EF1C", 0x6EF00, 0x6EF40, (0x6EF1C,0x6EF1F)), ("2E1C2", 0x2E1A0, 0x2E230, (0x2E1C2,0x2E1E8,0x2E20A)), ("105DA7", 0x105DA0, 0x105DB0, (0x105DA7,))]:
    P("=====", name); dump(lo, hi)
    for x in xs: xr(x)
out.close(); idc.qexit(0)
