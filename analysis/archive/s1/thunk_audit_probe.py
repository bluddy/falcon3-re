"""Read-only (DBFL_KILL): all 303 RTLink thunk slots - rec_id, far target seg:off, the variant segment the
rec_id selects (R<rec>_<seg-0x1000>[s]), its base, current crefs from the JMP FAR, and target state.
Output: analysis/s1/thunk_audit.json"""
import json, traceback
import idaapi, idc, idautils, ida_funcs, ida_bytes, ida_segment
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\thunk_audit.json"
LO, STRIDE, N = 0x2BD9D, 10, 303
R = {"slots": [], "segs": {}}
try:
    for s in idautils.Segments():
        sg = ida_segment.getseg(s)
        R["segs"][ida_segment.get_segm_name(sg)] = [sg.start_ea, sg.end_ea, ida_segment.get_segm_base(sg)]
    for i in range(N):
        s = LO + i * STRIDE
        b = idc.get_bytes(s, 10)
        f = ida_funcs.get_func(s)
        ch = []
        if f:
            it = ida_funcs.func_tail_iterator_t(f)
            ok = it.main()
            while ok:
                ch.append([it.chunk().start_ea, it.chunk().end_ea])
                ok = it.next()
        R["slots"].append({
            "slot": s, "bytes": b.hex(),
            "func": [f.start_ea, f.end_ea] if f else None, "chunks": ch,
            "crefs": [[x.to, x.type, bool(x.user)] for x in idautils.XrefsFrom(s + 3, 0) if x.iscode],
        })
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
