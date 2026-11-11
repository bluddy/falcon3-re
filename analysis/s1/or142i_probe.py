import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_ua, ida_funcs, idc, idaapi, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or142i.txt", "w")
def chunks(f):
    it = ida_funcs.func_tail_iterator_t(f); ok = it.main(); ch = []
    while ok:
        ch.append("%X-%X" % (it.chunk().start_ea, it.chunk().end_ea)); ok = it.next()
    return ch
for s in (0x6E8F0, 0x6E581):
    f = ida_funcs.get_func(s)
    out.write("fn %X..%X %s far=%s chunks=%s\n" % (f.start_ea, f.end_ea, idaapi.get_name(s), bool(f.flags & ida_funcs.FUNC_FAR), chunks(f)))
out.write("xrefs -> 6E8F0: %s\n" % [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x6E8F0, 0)])
out.write("xrefs -> 6E581: %s\n" % [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x6E581, 0)])
out.write("xrefs -> 6E64A: %s\n" % [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x6E64A, 0)])
out.write("xrefs -> 6E6BC: %s\n" % [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x6E6BC, 0)])
out.write("raw 6E8B7..6E900: %s\n" % ida_bytes.get_bytes(0x6E8B7, 0x49).hex(" "))
a = ida_bytes.get_item_head(0x6E8B7)
while a < 0x6E930:
    out.write("  %X %-14s %s\n" % (a, ida_bytes.get_bytes(a, ida_bytes.get_item_size(a)).hex(), idc.generate_disasm_line(a, 0)[:70])); a += ida_bytes.get_item_size(a)
out.write("raw 6E540..6E600: %s\n" % ida_bytes.get_bytes(0x6E540, 0xC0).hex(" "))
a = ida_bytes.get_item_head(0x6E540)
while a < 0x6E590:
    out.write("  %X %-14s %s\n" % (a, ida_bytes.get_bytes(a, ida_bytes.get_item_size(a)).hex(), idc.generate_disasm_line(a, 0)[:70])); a += ida_bytes.get_item_size(a)
out.close(); idc.qexit(0)
