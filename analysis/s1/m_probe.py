import idc, idaapi
open(r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\m_probe.txt","w").write("\n".join(idc.generate_disasm_line(a,0) for a in (0x42F6A,)))
idaapi.set_database_flag(idaapi.DBFL_KILL); idc.qexit(0)
