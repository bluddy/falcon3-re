import idc, idaapi, ida_funcs, ida_bytes, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\disp_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
def dump(lo, hi):
    a = lo
    while a < hi:
        h = ida_bytes.get_item_head(a); f = ida_funcs.get_func(h)
        P("%X %-7s %-40s %s" % (h, "%X" % f.start_ea if f else "-", idc.generate_disasm_line(h, 0)[:40], " ".join("%02X" % ida_bytes.get_byte(h+i) for i in range(min(ida_bytes.get_item_size(h), 6)))))
        a = h + max(ida_bytes.get_item_size(h), 1)
P("== 106A17 table"); dump(0x106A00, 0x106A3A)
P("== dispatch region words at cs:0C24..0C40 (seg base 0x100000?)")
base = 0x106A17
P("word dump 0x106A00..0x106A60:", " ".join("%04X" % ida_bytes.get_word(a) for a in range(0x106A00, 0x106A40, 2)))
P("== 0x106A3A..0x106AA0"); dump(0x106A3A, 0x106AA0)
P("== table 0x105D90.. words"); P(" ".join("%04X" % ida_bytes.get_word(a) for a in range(0x105D90, 0x105DD0, 2)))
P("name at 106A17:", idc.get_name(0x106A17), "xrefs", [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x106A17, 0)])
P("0x105D9D func:", idc.get_func_name(0x105D9D), "ea 105D9D xrefs", [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x105D9D, 0)])
P("== 105D9D..105DA9 bytes", " ".join("%02X" % ida_bytes.get_byte(a) for a in range(0x105D80, 0x105DB0)))
out.close(); idc.qexit(0)
