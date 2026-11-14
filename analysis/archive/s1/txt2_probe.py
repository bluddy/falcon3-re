import os
os.environ["DBFL_KILL"] = "1"
import ida_auto, ida_bytes, idautils, idc, ida_funcs

ida_auto.auto_wait()
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\txt2_probe.txt", "w")
LO, HI = 0x105DE6, 0x10626E
bs = ida_bytes.get_bytes(LO, HI - LO)
# parse: control byte (1..0x1f) alone, otherwise NUL-terminated string
starts, a = [], LO
while a < HI:
    b = bs[a - LO]
    if 0 < b < 0x20:
        starts.append((a, "b", 1)); a += 1
    else:
        e = bs.index(b"\x00", a - LO) + 1 + 0
        starts.append((a, "s", e - (a - LO))); a = LO + e
out.write("parse items: %d, end %X\n" % (len(starts), a))
sset = {s[0] for s in starts}
# table targets
tab = [ida_bytes.get_word(0x105D90 + i) for i in range(0, 0x56, 2)]
bad = []
for i, w in enumerate(tab):
    t = 0x105D90 + w
    out.write("tab[%d] = %04X -> %X %s\n" % (i, w, t, "start" if t in sset else "NOT START"))
for s in starts[:6]:
    out.write("%X %s %d\n" % s)
nonascii = [hex(LO + i) for i, c in enumerate(bs) if c >= 0x7f]
out.write("non-ascii bytes: %s\n" % nonascii)
out.write("\n1073F2 area:\n")
for h in range(0x1073E0, 0x107400):
    pass
ea = 0x1073F2
out.write("%X flags %X %s\n" % (ea, ida_bytes.get_flags(ea), idc.generate_disasm_line(ea, 0)))
f = ida_funcs.get_func(ea)
out.write("fn %s\n" % (hex(f.start_ea) if f else None))
for r in idautils.XrefsFrom(ea, 0):
    out.write("from: %X type %d\n" % (r.to, r.type))
for r in idautils.XrefsTo(0x10614A, 0):
    out.write("to 10614A: %X %d\n" % (r.frm, r.type))
out.close()
idc.qexit(0)
