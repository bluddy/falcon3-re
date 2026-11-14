import os
os.environ["DBFL_KILL"] = "1"
import ida_funcs, idautils, idc
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or143c.txt", "w")
for t in (0x155F2A, 0x155F18, 0x12BF96, 0x12BFA8, 0x155D10, 0x155DC1):
    out.write("xrefs to %X: %s\n" % (t, [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0)]))
for a in (0x155D10, 0x155DC1):
    f = ida_funcs.get_func(a); out.write("%X in %s: %s\n" % (a, hex(f.start_ea) if f else None, idc.generate_disasm_line(a, 0)))
out.close(); idc.qexit(0)
