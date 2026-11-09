import idaapi, ida_segregs
ROOT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit"
out=[]
rr = ida_segregs.sreg_range_t()
for ea in (0x327A0,0x327B2,0x3BBF0,0x3BBFF):
    for r in ("es","ds"):
        g=idaapi.str2reg(r); ida_segregs.get_sreg_range(rr, ea, g)
        out.append("%X %s %X..%X v%X t%d"%(ea,r,rr.start_ea,rr.end_ea,rr.val,rr.tag))
open(ROOT+r"\exp_sreg2.txt","w").write("\n".join(out)); idaapi.qexit(0)
