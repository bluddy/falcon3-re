"""Read-only (DBFL_KILL): for each fl_F continuation, the last ~6 items of the predecessor and the orphan run
(first 14 / last 4 items) with owner, kind and non-flow xrefs.  Output: analysis/s1/cont_dis.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\cont_dis.txt"
RUNS = [(0x10CC8E, 0x10CE05), (0x105DA9, 0x105EB5), (0x215FE, 0x21631), (0x2D353, 0x2D375), (0x6EC17, 0x6EC2B),
        (0x6EF1F, 0x6EF2F), (0x2E1E8, 0x2E1F3), (0x167449, 0x167450), (0x22C8B, 0x22C91), (0x25220, 0x25224),
        (0x67F77, 0x67F79), (0x69720, 0x69722), (0x3F6C7, 0x3F6D6), (0x100DED, 0x100DFA), (0x4334E, 0x4335A),
        (0x1093A6, 0x1093A8), (0x12BF89, 0x12BFE1)]
L = []


def line(a):
    g = ida_funcs.get_func(a)
    fl = ida_bytes.get_flags(a)
    xs = ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0) if x.type != 21]
    return "%X [%s]%s %s %s" % (a, ("%X" % g.start_ea) if g else "-", "C" if ida_bytes.is_code(fl) else "D",
                                idc.generate_disasm_line(a, 0), ("<- " + ",".join(xs[:4])) if xs else "")


try:
    for lo, hi in RUNS:
        L.append("=== %X..%X" % (lo, hi))
        p, pre = lo, []
        for _ in range(6):
            p = idc.prev_head(p, 0)
            pre.append(p)
        for p in reversed(pre):
            L.append("  pre " + line(p))
        heads, a = [], lo
        while a < hi:
            heads.append(a)
            a += max(ida_bytes.get_item_size(a), 1)
        for h in heads[:14]:
            L.append("      " + line(h))
        if len(heads) > 18:
            L.append("      ... (%d heads)" % len(heads))
        for h in heads[max(14, len(heads) - 4):]:
            L.append("      " + line(h))
        L.append("  next " + line(hi))
        L.append("")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
