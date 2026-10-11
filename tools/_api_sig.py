import ida_segment, idaapi
open(r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\api_sig.txt","w").write(
    (ida_segment.add_segm.__doc__ or "no doc") + "\n---\n" +
    (ida_segment.add_segm_ex.__doc__ or "no doc") + "\n---\n" +
    str(ida_segment.get_segm_qty.__doc__))
idaapi.qexit(0)
