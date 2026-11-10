import idaapi, idc, ida_segregs, ida_segment, ida_funcs
OUT=r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\post.txt"
DS=idaapi.str2reg("ds"); L=[]
rr=ida_segregs.sreg_range_t()
for a in (0x106EE2,0x106EEC,0x108430,0x10CE30):
    ida_segregs.get_sreg_range(rr,a,DS)
    L.append("DS@%X range %X..%X tag %d val %s" % (a, rr.start_ea, rr.end_ea, rr.tag, None if rr.val in (idaapi.BADSEL,) else hex(ida_segment.sel2para(rr.val))))
for a in (0x106EE2,0x108430,0x10CE30,0x10931E,0x109445,0x129F7,0x12B12):
    f=ida_funcs.get_func(a); L.append("%X %X-%X flags %X name %s" % (a,f.start_ea,f.end_ea,f.flags,idaapi.get_name(a)))
open(OUT,"w").write("\n".join(L)); idaapi.set_database_flag(idaapi.DBFL_KILL); idc.qexit(0)
