import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi, ida_segment

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or141.txt", "w")


def dump(lo, hi):
    a = ida_bytes.get_item_head(lo)
    while a < hi:
        f = ida_funcs.get_func(a)
        sz = max(ida_bytes.get_item_size(a), 1)
        out.write("   %X %-6s %-14s %s\n" % (a, hex(f.start_ea) if f else "-", ida_bytes.get_bytes(a, sz).hex()[:14], idc.generate_disasm_line(a, 0)[:70]))
        a += sz


for lo, hi in ((0x1004C0, 0x100510), (0x10059E, 0x1005C0)):
    out.write("--- %X..%X\n" % (lo, hi))
    dump(lo, hi)
for t in (0x100505, 0x10059F, 0x100500):
    out.write("xrefs -> %X: %s\n" % (t, [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0)]))
out.write("seg %s\n" % ida_segment.get_segm_name(ida_segment.getseg(0x100505)))
out.close()
idc.qexit(0)
