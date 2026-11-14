import os
os.environ["DBFL_KILL"] = "1"
import ida_funcs, ida_segment, idc, idautils
out = open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\or141d.txt", "w")
f = ida_funcs.get_func(0x100457)
it = ida_funcs.func_tail_iterator_t(f); ok = it.main(); ch = []
while ok:
    ch.append("%X-%X" % (it.chunk().start_ea, it.chunk().end_ea)); ok = it.next()
out.write("fn %X..%X flags=%X chunks=%s\n" % (f.start_ea, f.end_ea, f.flags, ch))
s = ida_segment.getseg(0x100457)
out.write("seg %s start=%X sel para=%X\n" % (ida_segment.get_segm_name(s), s.start_ea, ida_segment.sel2para(s.sel)))
for a in (0x100457, 0x1004E4, 0x100502):
    out.write("%X %s\n" % (a, idc.generate_disasm_line(a, 0)))
out.write("data refs to 100457: %s\n" % [(hex(r.frm), r.type) for r in idautils.XrefsTo(0x100457, 0)])
out.close(); idc.qexit(0)
