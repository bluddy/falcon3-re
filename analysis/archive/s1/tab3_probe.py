import idc, idaapi, ida_funcs, ida_bytes, idautils, ida_segment
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\tab3_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
lo, hi = 0x105D90, 0x105F40
a = lo
while a < hi:
    h = ida_bytes.get_item_head(a); f = ida_funcs.get_func(h)
    fl = ida_bytes.get_flags(h)
    kind = "code" if ida_bytes.is_code(fl) else ("str" if ida_bytes.is_strlit(fl) else ("data" if ida_bytes.is_data(fl) else "unk"))
    if a < 0x105DE0 or a > 0x105E90 or kind == "str" or idc.get_name(h):
        P("%X %-4s sz%-3d %-30s %s" % (h, kind, ida_bytes.get_item_size(h), idc.generate_disasm_line(h, 0)[:30], idc.get_name(h)))
    a = h + max(ida_bytes.get_item_size(h), 1)
P("words 105DA9.. :", " ".join("%04X" % ida_bytes.get_word(x) for x in range(0x105DA9, 0x105EB5, 2)))
P("ascii 105EA0..:", bytes(ida_bytes.get_byte(x) for x in range(0x105E80, 0x105F40)))
refs = []
for x in range(lo, hi):
    for r in idautils.XrefsTo(x, 0):
        if not (lo <= r.frm < hi): refs.append((hex(r.frm), hex(x), r.type))
P("xrefs into region from outside:", refs[:60])
P("code heads in region:", sum(1 for x in range(lo, hi) if ida_bytes.is_code(ida_bytes.get_flags(x)) and ida_bytes.get_item_head(x) == x))
P("1069B4..1069C8:", [(hex(x), idc.generate_disasm_line(x,0)[:30], ida_bytes.get_item_size(x)) for x in range(0x1069B4, 0x1069C8, 2)])
out.close(); idc.qexit(0)
