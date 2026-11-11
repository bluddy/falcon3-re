import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idc, idautils, idaapi
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or144d.txt", "w")
for ea in (0x2E20A, 0x166F80, 0x16781C):
    f = ida_funcs.get_func(ea)
    it = ida_funcs.func_tail_iterator_t(f); ch = []; ok = it.main()
    while ok:
        c = it.chunk(); ch.append("%X-%X" % (c.start_ea, c.end_ea)); ok = it.next()
    out.write("%X fn %X..%X name=%s chunks=%s\n" % (ea, f.start_ea, f.end_ea, idaapi.get_name(f.start_ea), ch))
for t in (0x16781C, 0x16781A, 0x167820, 0x2E281, 0x2E285, 0x2E22F, 0x2E236, 0x2E23B):
    out.write("xrefs to %X: %s\n" % (t, [(hex(x.frm), x.type) for x in idautils.XrefsTo(t, 0)]))
out.close(); idc.qexit(0)
