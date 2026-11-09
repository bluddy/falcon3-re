import idaapi, ida_segment, ida_segregs
ROOT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit"
out = []
ES = idaapi.str2reg("es")
rr = ida_segregs.sreg_range_t()
def rng(ea):
    ida_segregs.get_sreg_range(rr, ea, ES); return "%X..%X v%X t%d" % (rr.start_ea, rr.end_ea, rr.val, rr.tag)
p = ida_segment.getseg(0x4FD20)
ida_segment.set_segm_end(p.start_ea, 0x4FD20, ida_segment.SEGMOD_KEEP)
t = ida_segment.segment_t(); t.start_ea, t.end_ea = 0x4FD20, 0x4FD8D
t.sel = ida_segment.setup_selector(0x4FD2); t.bitness = 0; t.type = p.type; t.align=p.align; t.comb=p.comb; t.perm=p.perm
ida_segment.add_segm_ex(t, "X", "CODE", ida_segment.ADDSEG_NOTRUNC)
s = ida_segment.getseg(0x4FD20); s.bitness = 0
out.append("defaults %s" % [hex(s.defsr[i]) for i in range(len(s.defsr))][:8])
out.append("set_default BADSEL -> %s" % ida_segregs.set_default_sreg_value(s, ES, idaapi.BADSEL))
s = ida_segment.getseg(0x4FD20)
out.append("after def: %s" % rng(0x4FD28))
out.append("split 7A32 @4FD21 -> %s %s" % (ida_segregs.split_sreg_range(0x4FD21, ES, 0x7A32, 3), rng(0x4FD28)))
for tag in (3, 4, 1, 2):
    ok = ida_segregs.split_sreg_range(0x4FD29, ES, idaapi.BADSEL, tag)
    out.append("split BADSEL t%d -> %s %s | %s" % (tag, ok, rng(0x4FD29), rng(0x4FD28)))
    ida_segregs.del_sreg_range(0x4FD29, ES)
out.append("SR consts %s" % [(n, getattr(ida_segregs, n)) for n in dir(ida_segregs) if n.startswith("SR_")])
open(ROOT + r"\exp_sreg3.txt", "w").write("\n".join(out))
idaapi.qexit(0)
