import idc, idaapi, ida_funcs, ida_bytes, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\tab4_probe.txt", "w")
def P(*a): out.write(" ".join(str(x) for x in a) + "\n")
B = 0x105D90
ws = [ida_bytes.get_word(B + 2*i) for i in range(0x2B)]
P("43 words:", " ".join("%X" % w for w in ws))
P("sorted unique targets:", " ".join("%X" % w for w in sorted(set(ws))))
raw = bytes(ida_bytes.get_byte(x) for x in range(0x105DE6, 0x106300))
import re
P(raw.decode("latin1").encode("unicode_escape").decode()[:2600])
# what is after: first function / code boundary
nxt = [(hex(f), idc.get_func_name(f)) for f in idautils.Functions(0x105D00, 0x106400)]
P("functions in 105D00..106400:", nxt)
a = 0x105EB5; n = 0
while a < 0x106300 and n < 40:
    h = ida_bytes.get_item_head(a); fl = ida_bytes.get_flags(h)
    P("%X %s sz%d %s" % (h, "code" if ida_bytes.is_code(fl) else "data", ida_bytes.get_item_size(h), idc.generate_disasm_line(h, 0)[:30]))
    a = h + max(ida_bytes.get_item_size(h), 1); n += 1
out.close(); idc.qexit(0)
