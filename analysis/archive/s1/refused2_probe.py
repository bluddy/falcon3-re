"""Read-only (DBFL_KILL): facts for the refused call targets.  Output: analysis/s1/refused2.txt"""
import json, traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils, ida_nalt, ida_name
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\refused2.txt"
L = []


def chunks(f):
    out, it = [], ida_funcs.func_tail_iterator_t(f)
    ok = it.main()
    while ok:
        out.append("%X-%X" % (it.chunk().start_ea, it.chunk().end_ea))
        ok = it.next()
    return out


def xr(a):
    return ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0)]


def nxt(a):
    f = ida_funcs.get_next_func(a)
    return "%X" % f.start_ea if f else None


try:
    for a in (0x106EEC, 0x10843D):
        f = ida_funcs.get_func(a)
        L.append("%X name=%s end=%X flags=%X chunks=%s cmt=%r rcmt=%r" % (
            a, idaapi.get_name(a), f.end_ea, f.flags, chunks(f), idc.get_func_cmt(a, 0), idc.get_func_cmt(a, 1)))
        L.append("   xrefs to %s" % xr(a))
        L.append("   user-named: %s  type: %s" % (ida_name.is_uname(idaapi.get_name(a)), idc.get_type(a)))
    for a in (0x10CE30, 0x109445, 0x129F7, 0x10931E):
        L.append("%X next func start %s; prev func %s" % (a, nxt(a), "%X" % ida_funcs.get_prev_func(a).start_ea))
    L.append("--- 10CE30 .. 10CFB0 heads")
    a = 0x10CE30
    while a < 0x10CFB0:
        g = ida_funcs.get_func(a)
        xs = [x for x in xr(a) if not x.endswith("/21")]
        L.append("%X [%s] %s %s" % (a, ("%X" % g.start_ea) if g else "-", idc.generate_disasm_line(a, 0), ("<- " + ",".join(xs[:4])) if xs else ""))
        a += max(ida_bytes.get_item_size(a), 1)
    f = ida_funcs.get_func(0x10CFA6)
    L.append("10CFA6 func %s %X-%X name=%s" % (f is not None, f.start_ea, f.end_ea, idaapi.get_name(f.start_ea)))
    fb = json.load(open(r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\function_bytes.json"))
    for k, v in fb.items():
        if v["ea"] in (0x106EEC, 0x10843D, 0x10CFA6, 0x1093A8, 0x129F7):
            L.append("fb %s %s" % (k, {x: y for x, y in v.items() if x != "bytes"}))
    L.append("--- 10931E .. 1093A8 raw")
    a = 0x10937B
    while a < 0x1093A8:
        L.append(line if False else "%X %s %s" % (a, ida_bytes.get_bytes(a, max(ida_bytes.get_item_size(a), 1)).hex(), idc.generate_disasm_line(a, 0)))
        a += max(ida_bytes.get_item_size(a), 1)
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
