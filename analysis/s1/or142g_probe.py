import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idc, idautils, idaapi
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or142g.txt", "w")
BASE = 0x6E0B0
out.write("words 6E140..6E1C0 (as base-relative -> abs if in 6E69E..6E8B7)\n")
for a in range(0x6E140, 0x6E1C0, 2):
    w = ida_bytes.get_word(a)
    t = BASE + w
    out.write("%X %04X %s %s\n" % (a, w, ("-> %X" % t) if 0x6E69E <= t < 0x6E8B7 else "", idc.generate_disasm_line(a, 0)[:40]))
# dispatcher: any ff /4 or /2 with cs: prefix and disp32 in table
for a in range(0x6E0B0, 0x6F900):
    if ida_bytes.get_byte(a) == 0x2E and ida_bytes.get_byte(a + 1) == 0xFF and ida_bytes.get_byte(a + 2) in (0xA7, 0x97, 0xA6, 0x96, 0x67, 0x57):
        out.write("indirect at %X: %s\n" % (a, ida_bytes.get_bytes(a, 6).hex(" ")))
out.close(); idc.qexit(0)
