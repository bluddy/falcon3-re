import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, ida_ua, idautils, idc, idaapi, ida_name

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f67h_probe.txt", "w")
out.write("bytes 683B8..683E0: %s\n" % ida_bytes.get_bytes(0x683B8, 0x28).hex(" "))
out.write("before: 683BC %s size %d\n" % (idc.generate_disasm_line(0x683BC, 0), idc.get_item_size(0x683BC)))
for a in (0x683C5, 0x683C6, 0x683C7, 0x683C8):
    out.write("  head? %X flags %X\n" % (a, ida_bytes.get_flags(a)))
out.write("xrefs to 683C5: %s\n" % [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x683C5, 0)])
f = ida_funcs.get_func(0x683C5)
out.write("fn %X..%X name %s\n" % (f.start_ea, f.end_ea, idaapi.get_name(0x683C5)))
# try: what does a decode from 683C1 look like after clearing 683C1..683C8
ida_bytes.del_items(0x683C1, ida_bytes.DELIT_SIMPLE, 8)
for a in (0x683C1,):
    n = ida_ua.create_insn(a)
    out.write("create_insn %X -> %s  %s\n" % (a, n, idc.generate_disasm_line(a, 0)))
nx = 0x683C1 + n
for i in range(6):
    out.write("  %X %s\n" % (nx, idc.generate_disasm_line(nx, 0))); nx += max(idc.get_item_size(nx), 1)
out.write("\nxrefs to 683C5-region jumps from 67F58..683C1 flows (type 19/18) landing at/after 683C1:\n")
for t in range(0x683C1, 0x6940E):
    for r in idautils.XrefsTo(t, 0):
        if 0x67BAF <= r.frm < 0x683C1 and r.type in (18, 19):
            out.write("  %X -> %X type %d\n" % (r.frm, t, r.type))
out.close()
idc.qexit(0)
