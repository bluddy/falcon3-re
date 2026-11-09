import idaapi, ida_segment, ida_segregs, ida_bytes
ROOT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit"
out = []
ES = idaapi.str2reg("es"); DS = idaapi.str2reg("ds")
g = lambda ea: (hex(ida_segregs.get_sreg(ea, ES)), hex(ida_segregs.get_sreg(ea, DS)))
out.append("before 4FD28 %s 4FD29 %s" % (g(0x4FD28), g(0x4FD29)))
rr = ida_segregs.sreg_range_t()
ida_segregs.get_sreg_range(rr, 0x4FD29, ES); out.append("ES range %X..%X v%X t%d" % (rr.start_ea, rr.end_ea, rr.val, rr.tag))
ida_segregs.get_sreg_range(rr, 0x4FD20, ES); out.append("ES range@20 %X..%X v%X t%d" % (rr.start_ea, rr.end_ea, rr.val, rr.tag))
p = ida_segment.getseg(0x4FD20)
ida_segment.set_segm_end(p.start_ea, 0x4FD20, ida_segment.SEGMOD_KEEP)
t = ida_segment.segment_t(); t.start_ea, t.end_ea = 0x4FD20, 0x4FD8D
t.sel = ida_segment.setup_selector(0x4FD2); t.bitness = 0; t.type = p.type; t.align=p.align; t.comb=p.comb; t.perm=p.perm
out.append("add %s" % ida_segment.add_segm_ex(t, "X", "CODE", ida_segment.ADDSEG_NOTRUNC))
s = ida_segment.getseg(0x4FD20); s.bitness = 0
out.append("after add 4FD28 %s 4FD29 %s" % (g(0x4FD28), g(0x4FD29)))
for tag in (3, 2):
    r = ida_segregs.split_sreg_range(0x4FD29, ES, idaapi.BADSEL, tag)
    out.append("split BADSEL tag%d -> %s ; 4FD29 %s" % (tag, r, g(0x4FD29)))
r = ida_segregs.split_sreg_range(0x4FD29, ES, 0x1234, 3); out.append("split 1234 -> %s %s" % (r, g(0x4FD29)))
r = ida_segregs.split_sreg_range(0x4FD29, ES, idaapi.BADSEL, 3); out.append("split back BADSEL -> %s %s" % (r, g(0x4FD29)))
r = ida_segregs.split_sreg_range(0x4FD29, ES, 0xFFFF, 3); out.append("split FFFF -> %s %s" % (r, g(0x4FD29)))
ida_segregs.get_sreg_range(rr, 0x4FD29, ES); out.append("ES range %X..%X v%X t%d" % (rr.start_ea, rr.end_ea, rr.val, rr.tag))
open(ROOT + r"\exp_sreg.txt", "w").write("\n".join(out))
idaapi.qexit(0)
