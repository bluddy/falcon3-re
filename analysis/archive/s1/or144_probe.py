import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idc, idaapi, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or144.txt", "w")
def dump(lo, hi):
    a = ida_bytes.get_item_head(lo)
    while a < hi:
        n = ida_bytes.get_item_size(a)
        f = ida_funcs.get_func(a)
        out.write("%X %-20s %s%s\n" % (a, ida_bytes.get_bytes(a, n).hex(), idc.generate_disasm_line(a, 0)[:70], "" if not f else "  [fn %X]" % f.start_ea))
        a += n
for name, lo, hi in (("1982F", 0x19800, 0x19860), ("1277CC", 0x1277A0, 0x1277F0), ("6EA3B", 0x6EA30, 0x6EA50), ("5DA68", 0x5DA50, 0x5DA80)):
    out.write("=== %s\n" % name); dump(lo, hi)
    t = {"1982F":0x1982F,"1277CC":0x1277CC,"6EA3B":0x6EA3B,"5DA68":0x5DA68}[name]
    out.write("xrefs: %s\n" % [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0)])
out.close(); idc.qexit(0)
