"""Read-only: every direct far call/jmp (9A/EA) in the IDB; decode seg:off, current crefs,
and the head/function status of the target under each 0x1E10 variant."""
import json, struct, traceback
import idaapi, idautils, idc, ida_bytes, ida_funcs, ida_segment, ida_ua, ida_xref
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\farcall_probe.json"
V = {"R05": (0x2e100, 0x388f0), "R27": (0x10c9e0, 0x4b40), "R28": (0x111530, 0xae80), "R29": (0x11c3c0, 0x388f0)}
R = {"calls": []}


def st(ea):
    fl = ida_bytes.get_flags(ea)
    f = ida_funcs.get_func(ea)
    return {"code": ida_bytes.is_code(fl), "head": ida_bytes.get_item_head(ea) == ea and ida_bytes.is_code(fl),
            "fs": bool(f and f.start_ea == ea), "fin": f.start_ea if f else None,
            "seg": ida_segment.get_segm_name(ida_segment.getseg(ea)) if ida_segment.getseg(ea) else None}


try:
    for s in idautils.Segments():
        g = ida_segment.getseg(s)
        ea = g.start_ea
        while ea != idaapi.BADADDR and ea < g.end_ea:
            fl = ida_bytes.get_flags(ea)
            if ida_bytes.is_code(fl):
                b0 = ida_bytes.get_byte(ea)
                if b0 in (0x9A, 0xEA) and ida_bytes.get_item_size(ea) == 5:
                    off, seg = struct.unpack("<HH", idc.get_bytes(ea, 5)[1:])
                    lin = (seg << 4) + off
                    refs = [(x.to, x.type, x.user) for x in idautils.XrefsFrom(ea, ida_xref.XREF_FAR) if x.iscode]
                    f = ida_funcs.get_func(ea)
                    rec = {"ea": ea, "op": b0, "off": off, "seg": seg, "lin": lin, "refs": refs,
                           "cseg": ida_segment.get_segm_name(g), "infn": f.start_ea if f else None, "var": {}}
                    for n, (b, l) in V.items():
                        o = lin - 0x2e100
                        if 0 <= o < l:
                            rec["var"][n] = [b + o, st(b + o)]
                    rec["lin_st"] = st(lin)
                    R["calls"].append(rec)
            ea = idc.next_head(ea, g.end_ea)
except Exception:
    R["error"] = traceback.format_exc()
open(OUT, "w").write(json.dumps(R))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
