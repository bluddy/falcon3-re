import idaapi, ida_segregs, os
ROOT = r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit"
out=[]
for ea in (0x327B2,0x3BBFF,0x3BC05,0x2EAAD,0x4FD29):
    out.append("%X %s"%(ea,[hex(ida_segregs.get_sreg(ea,idaapi.str2reg(r))) for r in ("es","ds","cs")]))
open(ROOT+"\\"+os.environ["SOUT"],"w").write("\n".join(out)); idaapi.qexit(0)
