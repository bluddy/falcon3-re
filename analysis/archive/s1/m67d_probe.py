import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\m67d_probe.txt", "w")
for fs in idautils.Functions(0x66000, 0x69500):
    f = ida_funcs.get_func(fs)
    it = ida_funcs.func_tail_iterator_t(f)
    ch, ok = [], it.main()
    while ok:
        c = it.chunk(); ch.append("%X-%X" % (c.start_ea, c.end_ea)); ok = it.next()
    xs = [(hex(r.frm), r.type) for r in idautils.XrefsTo(fs, 0)]
    out.write("%X..%X %-34s chunks=%s xrefs=%s\n" % (fs, f.end_ea, idaapi.get_name(fs), ch if len(ch) > 1 else "", xs[:5]))
out.close()
idc.qexit(0)
