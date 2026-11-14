import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idc, idaapi, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or143.txt", "w")
def dump(lo, hi):
    a = lo
    while a < hi:
        n = ida_bytes.get_item_size(a)
        f = ida_funcs.get_func(a)
        out.write("%X %-24s %s%s\n" % (a, ida_bytes.get_bytes(a, n).hex(), idc.generate_disasm_line(a, 0)[:70], "" if not f else "  [fn %X]" % f.start_ea))
        a += n
for name, lo, hi in (("12BF89", 0x12BF60, 0x12C010), ("155F1A", 0x155EF0, 0x155F60)):
    out.write("=== %s\n" % name); dump(lo, hi)
    xs = [(hex(r.frm), r.type) for r in idautils.XrefsTo(lo + (0x29 if name=="12BF89" else 0x2A), 0)]
    out.write("xrefs: %s\n" % xs)
for t in (0x12BF89, 0x155F1A):
    out.write("xrefs to %X: %s\n" % (t, [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0)]))
out.close(); idc.qexit(0)
