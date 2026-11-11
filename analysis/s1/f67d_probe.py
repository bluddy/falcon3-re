import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f67d_probe.txt", "w")
a = 0x67BAF
n = 0
while n < 14:
    f = ida_funcs.get_func(a)
    if not f:
        out.write("%X: no function\n" % a)
        break
    xs = [(hex(r.frm), r.type) for r in idautils.XrefsTo(a, 0)]
    ch = []
    it = ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        c = it.chunk(); ch.append("%X-%X" % (c.start_ea, c.end_ea)); ok = it.next()
    last = idc.prev_head(f.end_ea, f.start_ea)
    out.write("fn %X..%X name=%s chunks=%s\n   xrefs=%s\n   last: %X %s\n" % (f.start_ea, f.end_ea, idaapi.get_name(f.start_ea), ch, xs, last, idc.generate_disasm_line(last, 0)))
    a = f.end_ea
    n += 1
    m = idc.print_insn_mnem(last)
    if m in ("retf", "retn", "iret") or (m == "jmp" and n > 1 and False):
        out.write("   TERMINATOR\n")
        break
out.close()
idc.qexit(0)
