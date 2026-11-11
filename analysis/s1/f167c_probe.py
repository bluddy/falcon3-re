import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, ida_name, ida_ua, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f167c_probe.txt", "w")


def chunks(ea):
    f = ida_funcs.get_func(ea)
    it = ida_funcs.func_tail_iterator_t(f)
    ch, ok = [], it.main()
    while ok:
        c = it.chunk(); ch.append("%X-%X" % (c.start_ea, c.end_ea)); ok = it.next()
    return ch


out.write("before: %s\n" % chunks(0x166F80))
out.write("del_func frag: %s\n" % ida_funcs.del_func(0x167440))
ida_name.set_name(0x167440, "", ida_name.SN_NOWARN)
out.write("after del: %s  fn@1673D0=%s\n" % (chunks(0x166F80), ida_funcs.get_func(0x1673D0)))
ida_bytes.del_items(0x16743E, ida_bytes.DELIT_SIMPLE, 0x167450 - 0x16743E)
a = 0x16743E
while a < 0x167450:
    n = ida_ua.create_insn(a)
    out.write("create_insn %X -> %d\n" % (a, n))
    if n <= 0:
        break
    a += n
out.write("heads end at %X\n" % a)
for lo in (0x16740F, 0x167450):
    out.write("remove_func_tail %X: %s\n" % (lo, ida_funcs.remove_func_tail(ida_funcs.get_func(0x166F80), lo)))
out.write("after tails removed: %s\n" % chunks(0x166F80))
f = ida_funcs.get_func(0x166F80)
out.write("set_func_end 16781A: %s\n" % ida_funcs.set_func_end(0x166F80, 0x16781A))
out.write("after end: %s  flags=%X\n" % (chunks(0x166F80), ida_funcs.get_func(0x166F80).flags))
a = 0x1673D0
while a < 0x167450:
    f = ida_funcs.get_func(a)
    out.write("%X fn=%s %s\n" % (a, hex(f.start_ea) if f else "-", idc.generate_disasm_line(a, 0)))
    a += max(idc.get_item_size(a), 1)
out.close()
idc.qexit(0)
