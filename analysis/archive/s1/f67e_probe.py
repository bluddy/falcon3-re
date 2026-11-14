import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f67e_probe.txt", "w")
a = 0x67F58
seen = 0
while a < 0x68400 and seen < 40:
    f = ida_funcs.get_func(a)
    if f and f.start_ea == a:
        xs = [(hex(r.frm), r.type) for r in idautils.XrefsTo(a, 0)]
        last = idc.prev_head(f.end_ea, f.start_ea)
        out.write("fn %X..%X %s  xrefs=%s\n    last %X %s\n" % (f.start_ea, f.end_ea, idaapi.get_name(f.start_ea), xs, last, idc.generate_disasm_line(last, 0)))
        a = f.end_ea
    else:
        fl = ida_bytes.get_flags(a)
        out.write("%X %s fn=%s %s\n" % (a, "code" if ida_bytes.is_code(fl) else "data", hex(f.start_ea) if f else "-", idc.generate_disasm_line(a, 0)))
        a += max(ida_bytes.get_item_size(a), 1)
    seen += 1
out.write("\nxrefs into 67BAF..68400 from outside, non-flow:\n")
for t in range(0x67BAF, 0x68400):
    for r in idautils.XrefsTo(t, 0):
        if not (0x67BAF <= r.frm < 0x68400) and r.type != 21:
            out.write("  %X -> %X type %d\n" % (r.frm, t, r.type))
out.write("\nretf/retn heads in 67F58..68400:\n")
for h in idautils.Heads(0x67F58, 0x68400):
    if idc.print_insn_mnem(h) in ("retf", "retn", "iret"):
        out.write("  %X %s\n" % (h, idc.generate_disasm_line(h, 0)))
out.close()
idc.qexit(0)
