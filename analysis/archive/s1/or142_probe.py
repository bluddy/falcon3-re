import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, ida_ua, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or142.txt", "w")


def dump(lo, hi):
    a = ida_bytes.get_item_head(lo)
    while a < hi:
        f = ida_funcs.get_func(a)
        sz = max(ida_bytes.get_item_size(a), 1)
        out.write("   %X %-7s %-14s %s\n" % (a, hex(f.start_ea) if f else "-", ida_bytes.get_bytes(a, sz).hex()[:14], idc.generate_disasm_line(a, 0)[:72]))
        a += sz


out.write("--- 6E700..6E7C7\n"); dump(0x6E700, 0x6E7C7)
out.write("--- 6E7C7..6E830\n"); dump(0x6E7C7, 0x6E830)
for t in (0x6E7C0, 0x6E7C2, 0x6E7C5, 0x6E7C6, 0x6E7C7, 0x6E7C8, 0x6E7CA, 0x6E7CC, 0x6E7CF, 0x6E7D5):
    out.write("xrefs -> %X: %s\n" % (t, [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0)]))
for s in idautils.Functions(0x6E600, 0x6E900):
    f = ida_funcs.get_func(s); out.write("  fn %X..%X %s\n" % (s, f.end_ea, idaapi.get_name(s)))
out.close(); idc.qexit(0)
