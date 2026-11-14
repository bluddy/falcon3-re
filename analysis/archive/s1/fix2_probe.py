import idc, idaapi, ida_funcs, ida_bytes, idautils, ida_xref, ida_name
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\fix2_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
def xin(lo, hi):
    return sorted((hex(r.frm), hex(x), r.type) for x in range(lo, hi) for r in idautils.XrefsTo(x, 0) if not (lo <= r.frm < hi))
ida_bytes.del_items(0x1069B4, ida_bytes.DELIT_SIMPLE, 20)
for a in range(0x1069B4, 0x1069BE, 2):
    ida_bytes.create_word(a, 2); idc.op_plain_offset(a, 0, 0x105D90)
for a in range(0x1069BE, 0x1069C8, 2): ida_bytes.create_word(a, 2)
for ea in (0x105DA7, 0x105D9D): ida_funcs.del_func(ea); ida_name.set_name(ea, "", ida_name.SN_NOWARN)
ida_bytes.del_items(0x105D90, ida_bytes.DELIT_SIMPLE, 0x105DE6 - 0x105D90)
for a in range(0x105D90, 0x105DE6, 2): ida_bytes.create_word(a, 2)
P("xin before cref removal:", xin(0x105D90, 0x105EB5))
for frm in (0x106A17, 0x106A4C, 0x106A7E):
    for to in (0x105D9D, 0x105DA7):
        P("del_cref", hex(frm), hex(to), ida_xref.del_cref(frm, to, 0))
P("xin after:", xin(0x105D90, 0x105EB5))
for frm in (0x106A17, 0x106A4C):
    P("from %X:" % frm, sorted((hex(r.to), r.type) for r in idautils.XrefsFrom(frm, 0)))
for a in range(0x1069B4, 0x1069C8, 2): P("%X %s" % (a, idc.generate_disasm_line(a, 0)))
P("funcs in 105D00..106400:", [hex(f) for f in idautils.Functions(0x105D00, 0x106400)])
P("code heads 105D90..105DE6:", sum(1 for x in range(0x105D90, 0x105DE6) if ida_bytes.is_code(ida_bytes.get_flags(x))))
out.close(); idc.qexit(0)
