"""Read-only (DBFL_KILL): layout of 0x12C500..0x12CEA0 -- functions and orphan runs interleaved, with every
xref into each, and for each orphan run its first/last 4 lines.  Output: analysis/s1/cluster.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\cluster.txt"
LO, HI = 0x12C500, 0x12CEA0
L = []


def line(a):
    g = ida_funcs.get_func(a)
    return "%X [%s] %s" % (a, ("%X" % g.start_ea) if g else "-", idc.generate_disasm_line(a, 0))


try:
    a = ida_bytes.get_item_head(LO)
    segs = []
    while a < HI:
        g = ida_funcs.get_func(a)
        own = g.start_ea if g else None
        sz = max(ida_bytes.get_item_size(a), 1)
        code = ida_bytes.is_code(ida_bytes.get_flags(a))
        key = (own, code)
        if segs and segs[-1][0] == key:
            segs[-1][2] = a + sz
            segs[-1][3].append(a)
        else:
            segs.append([key, a, a + sz, [a]])
        a += sz
    for key, lo, hi, heads in segs:
        own, code = key
        L.append("--- %X..%X %s %s" % (lo, hi, "F=%X %s" % (own, idaapi.get_name(own)) if own else "ORPHAN" if code else "DATA", "(%d heads)" % len(heads)))
        if own is None and code:
            xs = []
            for h in heads:
                for x in idautils.XrefsTo(h, 0):
                    if not (lo <= x.frm < hi) and x.type != 21 or (x.type == 21 and not (lo <= x.frm < hi)):
                        xs.append("%X->%X/%d" % (x.frm, h, x.type))
            L.append("   xin: " + " ".join(xs[:12]))
            for h in heads[:5]:
                L.append("   " + line(h))
            L.append("   ...")
            for h in heads[-3:]:
                L.append("   " + line(h))
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
