import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or141b.txt", "w")
a = 0x100400
while a < 0x1004CB:
    f = ida_funcs.get_func(a)
    sz = max(ida_bytes.get_item_size(a), 1)
    out.write("%X %-7s %-16s %s\n" % (a, hex(f.start_ea) if f else "-", ida_bytes.get_bytes(a, sz).hex()[:16], idc.generate_disasm_line(a, 0)[:72]))
    a += sz
out.write("\nfunctions in 0x100000..0x1005A0:\n")
for s in idautils.Functions(0x100000, 0x1005A0):
    f = ida_funcs.get_func(s)
    out.write("  %X..%X %s\n" % (s, f.end_ea, idaapi.get_name(s)))
for t in (0x1004B6, 0x100502, 0x100522, 0x1004E4, 0x1004CB):
    out.write("xrefs -> %X: %s\n" % (t, [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0)]))
out.close()
idc.qexit(0)
