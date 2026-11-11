import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f67c_probe.txt", "w")
for lo, hi in ((0x67BAF, 0x67BE0), (0x67E30, 0x67E60), (0x68080, 0x68140)):
    a = lo
    while a < hi:
        f = ida_funcs.get_func(a)
        fl = ida_bytes.get_flags(a)
        out.write("%X %-4s fn=%s  %s\n" % (a, "code" if ida_bytes.is_code(fl) else "data", hex(f.start_ea) if f else "-", idc.generate_disasm_line(a, 0)))
        a += max(ida_bytes.get_item_size(a), 1)
    out.write("-----\n")
# all xrefs into 67BAF..68140 from outside
for t in range(0x67BAF, 0x68140):
    for r in idautils.XrefsTo(t, 0):
        if not (0x67BAF <= r.frm < 0x68140) and r.type != 21:
            out.write("xref %X -> %X type %d\n" % (r.frm, t, r.type))
# the inside jumps
for t in range(0x67BAF, 0x68140):
    for r in idautils.XrefsTo(t, 0):
        if (0x67BAF <= r.frm < 0x68140) and r.type in (16, 17, 18, 19):
            out.write("inner %X -> %X type %d\n" % (r.frm, t, r.type))
out.close()
idc.qexit(0)
