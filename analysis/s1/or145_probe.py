import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, ida_ua, idc, idautils, idaapi
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or145.txt", "w")
def chunks(ea):
    f = ida_funcs.get_func(ea); it = ida_funcs.func_tail_iterator_t(f); r = []; ok = it.main()
    while ok:
        r.append("%X-%X" % (it.chunk().start_ea, it.chunk().end_ea)); ok = it.next()
    return r
def redec(lo, hi, seeds):
    ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
    for s in seeds:
        a = s
        while a < hi:
            n = ida_ua.create_insn(a); out.write("  %X n=%d %s\n" % (a, n, idc.generate_disasm_line(a, 0)))
            if n <= 0: break
            m = idc.print_insn_mnem(a)
            a += n
            if m in ("jmp", "retn", "retf"): break
    return
f = 0x2E20A
out.write("before %s\n" % chunks(f))
redec(0x2E22F, 0x2E23D, [0x2E22F, 0x2E236])
redec(0x2E281, 0x2E28F, [0x2E281])
fn = ida_funcs.get_func(f)
out.write("tail1 %s\n" % ida_funcs.append_func_tail(fn, 0x2E22F, 0x2E23D)); out.write("  %s\n" % chunks(f))
fn = ida_funcs.get_func(f)
out.write("tail2 %s\n" % ida_funcs.append_func_tail(fn, 0x2E281, 0x2E28F)); out.write("  %s\n" % chunks(f))
fn = ida_funcs.get_func(f); out.write("main %X..%X\n" % (fn.start_ea, fn.end_ea))
out.close(); idc.qexit(0)
