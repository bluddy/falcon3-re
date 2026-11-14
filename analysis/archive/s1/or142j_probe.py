import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idc, idaapi, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or142j.txt", "w")
for a in (0x10B752, 0x10B757, 0x10B783, 0x10B77E, 0x1841A9, 0x184305, 0x6F6F7, 0x6EB0C):
    h = ida_bytes.get_item_head(a)
    out.write("%X: %s  | prev: %s\n" % (a, idc.generate_disasm_line(h, 0)[:80], idc.generate_disasm_line(idc.prev_head(h, 0), 0)[:60]))
    f = ida_funcs.get_func(a); out.write("      in fn %s\n" % (idaapi.get_name(f.start_ea) if f else None))
out.write("\nfunctions near 6E000..6F900:\n")
for s in idautils.Functions(0x6E000, 0x6F900):
    f = ida_funcs.get_func(s); out.write("  %X..%X %s\n" % (s, f.end_ea, idaapi.get_name(s)))
for t in (0x6E558, 0x6E54B, 0x6E64A, 0x6E6BC, 0x6E76A, 0x6E851):
    f = ida_funcs.get_func(t); out.write("owner(%X) = %s\n" % (t, hex(f.start_ea) if f else None))
out.close(); idc.qexit(0)
