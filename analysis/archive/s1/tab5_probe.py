import idc, idaapi, ida_funcs, ida_bytes, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\tab5_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
# find end of string area: scan from 0x105EB8 for the pusha (0x60) 06 1E B8 sequence
for a in range(0x105D90, 0x1069C8):
    if ida_bytes.get_bytes(a, 6) == b"\x60\x06\x1e\xb8\x9f\x70":
        P("code-looking start at %X" % a, "func", ida_funcs.get_func(a) and hex(ida_funcs.get_func(a).start_ea)); 
P("bytes around:", " ".join("%02X" % ida_bytes.get_byte(x) for x in range(0x1062F8, 0x106320)))
f = ida_funcs.get_func(0x10626E); P("sub_10626E", hex(f.start_ea), hex(f.end_ea))
for a in range(0x106260, 0x106290):
    pass
a = 0x106250
while a < 0x1062A0:
    h = ida_bytes.get_item_head(a); P("%X %s" % (h, idc.generate_disasm_line(h,0)[:40])); a = h + max(ida_bytes.get_item_size(h),1)
for x in (0x1069BE, 0x1069C0, 0x1069C2, 0x1069C4, 0x1069C6):
    P("%X" % x, idc.generate_disasm_line(x, 0), "word %04X" % ida_bytes.get_word(x), "refs from:", [(hex(r.to), r.type) for r in idautils.XrefsFrom(x, 0)])
P("callers of sub_10626E:", [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x10626E, 0)])
out.close(); idc.qexit(0)
