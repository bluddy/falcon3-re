"""Read-only (DBFL_KILL): owner bounds/chunks/names for the fl_F continuation candidates, plus the 0x100D00 region.
Output: analysis/s1/ext_plan.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\ext_plan.txt"
CAND = [(0x10CC60, 0x10CC8E, 0x10CE05), (0x2142E, 0x215FE, 0x21631), (0x2D31A, 0x2D353, 0x2D375),
        (0x3F6A9, 0x3F6C7, 0x3F6D6), (0x2520B, 0x25220, 0x25224)]
L = []


def chunks(f):
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append("%X-%X" % (it.chunk().start_ea, it.chunk().end_ea))
        ok = it.next()
    return out


def noncode(lo, hi):
    out, a = [], lo
    while a < hi:
        h = ida_bytes.get_item_head(a)
        if not ida_bytes.is_code(ida_bytes.get_flags(h)):
            out.append("%X" % h)
        a = h + max(ida_bytes.get_item_size(h), 1)
    return out


try:
    for fs, lo, hi in CAND:
        f = ida_funcs.get_func(fs)
        L.append("%X %s: func %X-%X flags=%X chunks=%s" % (fs, idaapi.get_name(fs), f.start_ea, f.end_ea, f.flags, chunks(f)))
        L.append("   run %X-%X noncode=%s owners=%s  last=%s" % (
            lo, hi, noncode(lo, hi), sorted({"%X" % ida_funcs.get_func(a).start_ea for a in range(lo, hi) if ida_funcs.get_func(a)}),
            idc.generate_disasm_line(idc.prev_head(hi, lo), 0)))
        ext = [x for x in idautils.XrefsTo(lo, 0) if x.type != 21]
        L.append("   xrefs to run start: %s" % [("%X/%d" % (x.frm, x.type)) for x in ext])
    L.append("--- 0x100D00 region")
    a = 0x100CC0
    while a < 0x100E00:
        g = ida_funcs.get_func(a)
        xs = ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0) if x.type != 21]
        L.append("%X [%s] %s %s" % (a, ("%X" % g.start_ea) if g else "-", idc.generate_disasm_line(a, 0), ("<- " + ",".join(xs[:3])) if xs else ""))
        a += max(ida_bytes.get_item_size(a), 1)
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
