import os
os.environ["DBFL_KILL"] = "1"
import ida_bytes, ida_funcs, idautils, idc, idaapi

out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\f67b_probe.txt", "w")
PRE = bytes.fromhex("b8947 88ec026a1f415ba1700f7eaba947 88ec226c41e2c1503d826c647".replace(" ", ""))
PRE = bytes.fromhex("b894788ec026a1f415ba1700f7eaba94788ec226c41e2c1503d826c647")
S = 0x1F
lo = 0x67F40
# walk back/forward in stamps
def stamp_at(a):
    b = ida_bytes.get_bytes(a, S)
    return b is not None and b[:len(PRE)] == PRE and b[len(PRE) + 1] == 0 and b[len(PRE)]
start = lo
while stamp_at(start - S) is not False and stamp_at(start - S):
    start -= S
end = lo
vals = []
while stamp_at(end):
    vals.append(stamp_at(end))
    end += S
out.write("stamp run %X..%X count %d fields %s\n" % (start, end, (end - start) // S, vals))
out.write("bytes after: %s\n" % ida_bytes.get_bytes(end, 24).hex(" "))
out.write("bytes before: %s\n" % ida_bytes.get_bytes(start - 24, 24).hex(" "))
out.write("\nfunctions/chunks in [%X, %X):\n" % (start - 0x40, end + 0x40))
seen = set()
for a in range(start - 0x40, end + 0x40):
    f = ida_funcs.get_func(a)
    if f and f.start_ea not in seen:
        seen.add(f.start_ea)
        out.write("  fn %X end %X name %s\n" % (f.start_ea, f.end_ea, idaapi.get_name(f.start_ea)))
        t = ida_funcs.func_tail_iterator_t(f)
        ok = t.main()
        while ok:
            c = t.chunk()
            out.write("      chunk %X..%X\n" % (c.start_ea, c.end_ea))
            ok = t.next()
out.write("\ncode heads count by kind:\n")
for fs in sorted(seen):
    for r in idautils.XrefsTo(fs, 0):
        out.write("  xref to %X from %X type %d\n" % (fs, r.frm, r.type))
out.write("\nfunction 67baf head xrefs:\n")
for r in idautils.XrefsTo(0x67BAF, 0):
    out.write("  from %X type %d\n" % (r.frm, r.type))
out.close()
idc.qexit(0)
