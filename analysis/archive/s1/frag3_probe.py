import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\frag3.txt"
L = []
def fn(a):
    f = ida_funcs.get_func(a)
    return ("%X-%X %s" % (f.start_ea, f.end_ea, idaapi.get_name(f.start_ea))) if f else "-"
def xr(a):
    return ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0)]
def chunks(a):
    f = ida_funcs.get_func(a)
    if not f: return None
    it = ida_funcs.func_tail_iterator_t(f); ok = it.main(); out = []
    while ok:
        out.append("%X-%X" % (it.chunk().start_ea, it.chunk().end_ea)); ok = it.next()
    return out
try:
    L.append("6EF30 xrefs %s ; 6EF31 xrefs %s ; func@6EF31 %s name %s" % (xr(0x6EF30), xr(0x6EF31), fn(0x6EF31), idaapi.get_name(0x6EF31)))
    L.append("6EC2C xrefs %s func %s" % (xr(0x6EC2C), fn(0x6EC2C)))
    L.append("bytes 6EC14: %s" % ida_bytes.get_bytes(0x6EC14, 0x1A).hex())
    L.append("bytes 6EF1C: %s" % ida_bytes.get_bytes(0x6EF1C, 0x18).hex())
    L.append("bytes 2E1C2: %s" % ida_bytes.get_bytes(0x2E1C2, 0x4C).hex())
    L.append("2E1C2 chunks %s ; 2E20A chunks %s ; 2E1C2 xrefs %s ; 2E20A xrefs %s" % (chunks(0x2E1C2), chunks(0x2E20A), xr(0x2E1C2), xr(0x2E20A)))
    L.append("22C91 xrefs %s ; 22C8E %s ; 22C8D %s" % (xr(0x22C91), xr(0x22C8E), xr(0x22C8D)))
    L.append("22C62 chunks %s; 22C91 chunks %s" % (chunks(0x22C62), chunks(0x22C91)))
    L.append("-- 69705 predecessor")
    x = 0x696E0
    while x < 0x69723:
        h = ida_bytes.get_item_head(x); sz = max(ida_bytes.get_item_size(h), 1)
        L.append("  %X %-14s %-36s %s" % (h, ida_bytes.get_bytes(h, sz).hex()[:28], idc.generate_disasm_line(h, 0)[:36], fn(h).split()[0])); x = h + sz
    L.append("xrefs 69705 %s; 6970A... 696FE func %s chunks %s" % (xr(0x69705), fn(0x696FE), chunks(0x696FE)))
    L.append("callers of 69705 / 69723: %s %s ; names %s %s" % (xr(0x69705), xr(0x69723), idaapi.get_name(0x69705), idaapi.get_name(0x69723)))
    L.append("-- 167420..167450")
    x = 0x167400
    while x < 0x167452:
        h = ida_bytes.get_item_head(x); sz = max(ida_bytes.get_item_size(h), 1)
        L.append("  %X %-14s %-36s %s" % (h, ida_bytes.get_bytes(h, sz).hex()[:28], idc.generate_disasm_line(h, 0)[:36], fn(h).split()[0])); x = h + sz
    L.append("166F80 chunks %s; 167440 chunks %s" % (chunks(0x166F80), chunks(0x167440)))
    L.append("-- 67F77 area; 67F59 chunks %s; 67F7B chunks %s; xrefs 67F7B %s 67F59 %s" % (chunks(0x67F59), chunks(0x67F7B), xr(0x67F7B), xr(0x67F59)))
    L.append("bytes 67F59: %s" % ida_bytes.get_bytes(0x67F59, 0x3E).hex())
    L.append("bytes 69705: %s" % ida_bytes.get_bytes(0x69705, 0x30).hex())
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
