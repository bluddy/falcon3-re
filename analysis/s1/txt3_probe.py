import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, idc

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\txt3_probe.txt", "w")
bad = 0
for i in range(0, 0x56, 2):
    w = ida_bytes.get_word(0x105D90 + i)
    t = 0x105D90 + w
    h = ida_bytes.get_item_head(t) == t
    s = ida_bytes.is_strlit(ida_bytes.get_flags(t))
    if not h:
        bad += 1
    out.write("%X -> %X head=%s strlit=%s %s\n" % (0x105D90 + i, t, h, s, idc.generate_disasm_line(t, 0)[:60]))
out.write("not-head targets: %d\n" % bad)
n = 0
a = 0x105DE6
while a < 0x10626E:
    n += 1
    a += ida_bytes.get_item_size(a)
out.write("items: %d, end %X\n" % (n, a))
out.close()
idc.qexit(0)
