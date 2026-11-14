import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f167_probe.txt", "w")
for fs in idautils.Functions(0x166000, 0x168400):
    f = ida_funcs.get_func(fs)
    it = ida_funcs.func_tail_iterator_t(f)
    ch, ok = [], it.main()
    while ok:
        c = it.chunk(); ch.append("%X-%X" % (c.start_ea, c.end_ea)); ok = it.next()
    out.write("fn %X..%X %s chunks=%s xrefs=%s\n" % (fs, f.end_ea, idaapi.get_name(fs), ch, [(hex(r.frm), r.type) for r in idautils.XrefsTo(fs, 0)][:4]))
out.write("\n")
a = 0x1673F0
while a < 0x167470:
    f = ida_funcs.get_func(a)
    fl = ida_bytes.get_flags(a)
    out.write("%X %-4s fn=%-8s %-14s %s | %s\n" % (a, "code" if ida_bytes.is_code(fl) else "data", hex(f.start_ea) if f else "-",
              ida_bytes.get_bytes(a, max(ida_bytes.get_item_size(a), 1)).hex(), idc.generate_disasm_line(a, 0), idaapi.get_name(a) or ""))
    a += max(ida_bytes.get_item_size(a), 1)
out.write("\n")
for t in range(0x167400, 0x167470):
    xs = [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0) if r.type != 21]
    if xs:
        out.write("xref -> %X: %s\n" % (t, xs))
out.close()
idc.qexit(0)
