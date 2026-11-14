import idaapi, ida_name
open(r"C:\Users\ybarnoy\projects\falcon3\analysis\segsplit\name.txt","w").write(ida_name.get_name(0x10002)); idaapi.qexit(0)
