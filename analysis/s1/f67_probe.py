import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f67_probe.txt", "w")
for fs in (0x67F59, 0x67F7B):
    f = ida_funcs.get_func(fs)
    out.write("== %X name=%s end=%X\n" % (fs, idaapi.get_name(fs), f.end_ea if f else 0))
    for r in idautils.XrefsTo(fs, 0):
        out.write("  xref to: %X type %d\n" % (r.frm, r.type))
out.write("\nbytes 67F40..67FC0\n")
bs = ida_bytes.get_bytes(0x67F40, 0x80)
for i in range(0, 0x80, 16):
    out.write("%X  %s\n" % (0x67F40 + i, bs[i:i + 16].hex(" ")))
a = 0x67F40
while a < 0x67FC0:
    fl = ida_bytes.get_flags(a)
    f = ida_funcs.get_func(a)
    out.write("%X %-8s fn=%s  %s\n" % (a, "code" if ida_bytes.is_code(fl) else "data", hex(f.start_ea) if f else "-", idc.generate_disasm_line(a, 0)))
    a += max(ida_bytes.get_item_size(a), 1)
for t in (0x67F77, 0x67F78, 0x67F79, 0x67F7A):
    for r in idautils.XrefsTo(t, 0):
        out.write("xref to %X from %X type %d\n" % (t, r.frm, r.type))
out.close()
idc.qexit(0)
