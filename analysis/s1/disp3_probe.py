import idc, idaapi, ida_funcs, ida_bytes, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\disp3_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
B = 0x105D90
for tab in (0x1069B4, 0x1069BE):
    P("table at %X:" % tab)
    for i in range(5):
        t = ida_bytes.get_word(tab + 2*i); ea = B + t; f = ida_funcs.get_func(ea)
        P("  [%d] %04X -> %X %-34s func %s name %s" % (i, t, ea, idc.generate_disasm_line(ea, 0)[:34], f and hex(f.start_ea), idc.get_name(ea)))
P("item @1069B4:", idc.generate_disasm_line(0x1069B4, 0), "@1069BE:", idc.generate_disasm_line(0x1069BE, 0), idc.generate_disasm_line(0x1069C8,0))
for ea in (0x105D9D, 0x105DA7):
    P("xrefs to %X:" % ea, [(hex(r.frm), r.type, idc.generate_disasm_line(r.frm,0)[:40]) for r in idautils.XrefsTo(ea, 0)])
P("callers/refs 1069C2:", idc.generate_disasm_line(0x1069C2, 0))
P("xrefs from 106A17:", [(hex(r.to), r.type) for r in idautils.XrefsFrom(0x106A17, 0)])
P("xrefs from 106A4C:", [(hex(r.to), r.type) for r in idautils.XrefsFrom(0x106A4C, 0)])
out.close(); idc.qexit(0)
