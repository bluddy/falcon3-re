import os, json
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or138b.txt", "w")


def chunks(f):
    it = ida_funcs.func_tail_iterator_t(f)
    ch, ok = [], it.main()
    while ok:
        c = it.chunk(); ch.append("%X-%X" % (c.start_ea, c.end_ea)); ok = it.next()
    return ch


def dump(lo, hi):
    a = lo
    while a < hi:
        f = ida_funcs.get_func(a)
        out.write("   %X %-6s %-16s %s\n" % (a, hex(f.start_ea) if f else "-", ida_bytes.get_bytes(a, max(ida_bytes.get_item_size(a), 1)).hex()[:16],
                  idc.generate_disasm_line(a, 0)[:70]))
        a += max(ida_bytes.get_item_size(a), 1)


for ea in (0x16F47D, 0x2C9F0):
    f = ida_funcs.get_func(ea)
    if not f: continue
    out.write("fn %X..%X %s chunks=%s\n" % (ea, f.end_ea, idaapi.get_name(ea), chunks(f)))
out.write("--- 16F47D tail\n")
dump(0x16F495, 0x16F4D0)
out.write("--- xrefs to 16F4B1\n")
for r in idautils.XrefsTo(0x16F4B1, 0):
    g = ida_funcs.get_func(r.frm)
    out.write("   %X type %d in %s\n" % (r.frm, r.type, hex(g.start_ea) if g else "-"))
out.write("--- 2CA17 context\n")
dump(0x2CA00, 0x2CA50)
for t in (0x2CA17, 0x2CA3F):
    out.write("xrefs -> %X: %s\n" % (t, [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0)]))
out.close()
idc.qexit(0)
