import idc, idaapi, ida_funcs, ida_bytes, idautils, ida_segregs, ida_segment
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\disp2_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
cs = idc.get_sreg(0x106A17, "cs"); P("cs at 106A17: %X" % cs, "base lin %X" % (cs*16))
seg = ida_segment.getseg(0x106A17); P("seg", hex(seg.start_ea), hex(seg.end_ea), idc.get_segm_name(0x106A17), "sel", hex(seg.sel))
for off in (0xC24, 0xC2E):
    P("cs:%X -> %X" % (off, cs*16+off))
b = cs*16
P("table0 words:", ["%04X" % ida_bytes.get_word(b+0xC24+2*i) for i in range(5)])
P("table1 words:", ["%04X" % ida_bytes.get_word(b+0xC2E+2*i) for i in range(5)])
for i in range(5):
    t = ida_bytes.get_word(b+0xC24+2*i); ea = b+t
    f = ida_funcs.get_func(ea)
    P("entry", i, hex(t), hex(ea), idc.generate_disasm_line(ea,0)[:40], "func", f and hex(f.start_ea), idc.get_name(ea))
P("items at table0:", [(hex(a), idc.get_item_head(a), ida_bytes.get_item_size(a)) for a in (b+0xC24, b+0xC2E)])
P("funcs near table:", [(hex(f), hex(ida_funcs.get_func(f).end_ea)) for f in idautils.Functions(b+0xC00, b+0xC40)])
P("surrounding funcs list 1069C8:", hex(ida_funcs.get_func(0x1069C8).start_ea), hex(ida_funcs.get_func(0x1069C8).end_ea))
out.close(); idc.qexit(0)
