import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\v22_probe.txt", "w")
for fs in idautils.Functions(0x22A00, 0x22E00):
    f = ida_funcs.get_func(fs)
    out.write("fn %X..%X %s xrefs=%s\n" % (fs, f.end_ea, idaapi.get_name(fs), [(hex(r.frm), r.type) for r in idautils.XrefsTo(fs, 0)][:6]))
out.write("\n")
a = 0x22C40
while a < 0x22CD0:
    f = ida_funcs.get_func(a)
    fl = ida_bytes.get_flags(a)
    out.write("%X %-4s fn=%-7s %-12s %s\n" % (a, "code" if ida_bytes.is_code(fl) else "data", hex(f.start_ea) if f else "-", ida_bytes.get_bytes(a, max(ida_bytes.get_item_size(a), 1)).hex(), idc.generate_disasm_line(a, 0)))
    a += max(ida_bytes.get_item_size(a), 1)
for t in range(0x22C62, 0x22CA0):
    for r in idautils.XrefsTo(t, 0):
        if not (0x22C62 <= r.frm < 0x22CA0):
            out.write("xref %X -> %X type %d\n" % (r.frm, t, r.type))
out.close()
idc.qexit(0)
