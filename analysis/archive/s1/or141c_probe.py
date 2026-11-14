import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_ua, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or141c.txt", "w")
for lo, hi in ((0x100457, 0x1004BF), (0x1004CB, 0x100505)):
    out.write("--- %X..%X\n" % (lo, hi))
    a = lo
    while a < hi:
        insn = ida_ua.insn_t()
        n = ida_ua.decode_insn(insn, a)
        if n <= 0:
            out.write("%X ??\n" % a); a += 1; continue
        out.write("%X %-14s %s\n" % (a, ida_bytes.get_bytes(a, n).hex(), idc.GetDisasm(a) if ida_bytes.is_code(ida_bytes.get_flags(a)) else "(dec) len %d mnem %s" % (n, insn.get_canon_mnem())))
        a += n
for t in (0x100457, 0x1004BE, 0x1004BF, 0x1004CB, 0x100596):
    out.write("xrefs -> %X: %s\n" % (t, [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0)]))
out.close()
idc.qexit(0)
