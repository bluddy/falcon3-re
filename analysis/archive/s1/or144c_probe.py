import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idc, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or144c.txt", "w")
for name, lo, hi in (("167822", 0x167800, 0x167850), ("2E235", 0x2E200, 0x2E2B0)):
    out.write("=== %s\n" % name)
    a = ida_bytes.get_item_head(lo)
    while a < hi:
        n = ida_bytes.get_item_size(a); f = ida_funcs.get_func(a)
        out.write("%X %-18s %-44s %s\n" % (a, ida_bytes.get_bytes(a, n).hex(), idc.generate_disasm_line(a, 0)[:44], "" if not f else "[fn %X]" % f.start_ea))
        a += n
for t in (0x2E235, 0x2E236, 0x2E286, 0x167822):
    out.write("xrefs to %X: %s\n" % (t, [(hex(x.frm), x.type) for x in idautils.XrefsTo(t, 0)]))
out.close(); idc.qexit(0)
