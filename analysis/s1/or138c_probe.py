import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or138c.txt", "w")
f = ida_funcs.get_func(0x16F4B5)
it = ida_funcs.func_tail_iterator_t(f)
ch, ok = [], it.main()
while ok:
    c = it.chunk(); ch.append("%X-%X" % (c.start_ea, c.end_ea)); ok = it.next()
out.write("fn %X..%X name=%s flags=%X chunks=%s\n" % (f.start_ea, f.end_ea, idaapi.get_name(0x16F4B5), f.flags, ch))
out.write("xrefs to 16F4B5: %s\n" % [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x16F4B5, 0)])
out.write("xrefs to 16F4B4: %s\n" % [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x16F4B4, 0)])
a = 0x16F4B1
while a < 0x16F4B8:
    out.write("%X %s\n" % (a, idc.generate_disasm_line(a, 0))); a += idc.get_item_size(a)
for lo in (0x1002C, 0x22AEB, 0x23E25, 0x2CA17, 0x12D15E):
    f = ida_funcs.get_func(lo)
    out.write("get_func(%X) = %s\n" % (lo, f))
out.close()
idc.qexit(0)
