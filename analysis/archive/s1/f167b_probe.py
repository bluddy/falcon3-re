import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f167b_probe.txt", "w")
a = 0x1673A0
while a < 0x1673F0:
    f = ida_funcs.get_func(a)
    fl = ida_bytes.get_flags(a)
    out.write("%X %-4s fn=%-8s %-14s %s | %s\n" % (a, "code" if ida_bytes.is_code(fl) else "data", hex(f.start_ea) if f else "-",
              ida_bytes.get_bytes(a, max(ida_bytes.get_item_size(a), 1)).hex(), idc.generate_disasm_line(a, 0), idaapi.get_name(a) or ""))
    a += max(ida_bytes.get_item_size(a), 1)
out.write("\n")
for t in (0x1673D0, 0x16740F, 0x167440, 0x167441, 0x167442, 0x167447, 0x167449, 0x16743E, 0x16744B, 0x167A8A):
    out.write("xrefs -> %X: %s\n" % (t, [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0)]))
for fs in (0x166F80, 0x167440):
    f = ida_funcs.get_func(fs)
    out.write("fn %X flags=%X end=%X name=%s\n" % (fs, f.flags, f.end_ea, idaapi.get_name(fs)))
    it = ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        c = it.chunk(); out.write("   chunk %X-%X\n" % (c.start_ea, c.end_ea)); ok = it.next()
out.write("bytes 16743E..167450: %s\n" % ida_bytes.get_bytes(0x16743E, 18).hex())
out.close()
idc.qexit(0)
