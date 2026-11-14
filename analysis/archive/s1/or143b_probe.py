import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idc, idaapi, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or143b.txt", "w")
for t in range(0x12BF86, 0x12BFE2):
    xs = [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0) if r.type != 21]
    if xs: out.write("xrefs to %X: %s\n" % (t, xs))
for t in range(0x155F14, 0x155F50):
    xs = [(hex(r.frm), r.type) for r in idautils.XrefsTo(t, 0) if r.type != 21]
    if xs: out.write("xrefs to %X: %s\n" % (t, xs))
for s in (0x155F4C, 0x155F4D, 0x12BFE1):
    f = ida_funcs.get_func(s); out.write("fn %X..%X %s flags=%X\n" % (f.start_ea, f.end_ea, idaapi.get_name(s), f.flags))
for s in idautils.Functions(0x155D00, 0x156100):
    f = ida_funcs.get_func(s); out.write("  %X..%X %s\n" % (s, f.end_ea, idaapi.get_name(s)))
out.write(ida_bytes.get_bytes(0x12BF2A, 0x10).hex() + "\n")
# table 12BF7C words
for a in range(0x12BF7C, 0x12BF98, 2):
    out.write("%X w=%04X -> %X\n" % (a, ida_bytes.get_word(a), 0x12B1F0 + ida_bytes.get_word(a)))
out.close(); idc.qexit(0)
