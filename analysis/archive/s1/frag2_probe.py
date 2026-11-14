import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\frag2.txt"
L = []
def fn(a):
    f = ida_funcs.get_func(a)
    return ("%X-%X %s" % (f.start_ea, f.end_ea, idaapi.get_name(f.start_ea))) if f else "-"
def dump(lo, hi):
    x = lo
    while x < hi:
        h = ida_bytes.get_item_head(x)
        sz = max(ida_bytes.get_item_size(h), 1)
        L.append("  %X %-14s %-36s %s%s" % (h, (ida_bytes.get_bytes(h, sz) or b"").hex()[:28], idc.generate_disasm_line(h, 0)[:36], fn(h).split()[0],
                                          "" if ida_bytes.is_code(ida_bytes.get_flags(h)) else " [D]"))
        x = h + sz
def words(lo, n):
    b = ida_bytes.get_bytes(lo, n * 2)
    L.append("  words @%X: %s" % (lo, " ".join("%04X" % (b[i] | b[i + 1] << 8) for i in range(0, len(b), 2))))
try:
    L.append("== 6EC14 table"); words(0x6EC14, 14); dump(0x6EC2B, 0x6EC30)
    L.append("   refs to 6EC14/6EC2C: %s %s" % (["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x6EC14, 0)], ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x6EC2C, 0)]))
    L.append("== 6EF1C table"); words(0x6EF1C, 12); dump(0x6EF2F, 0x6EF40)
    L.append("   refs to 6EF1C: %s ; 6EF30/31: %s" % (["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x6EF1C, 0)], ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x6EF30, 0)] + ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x6EF31, 0)]))
    L.append("== 2E1C2"); words(0x2E1C2, 40); dump(0x2E1E8, 0x2E260)
    L.append("   refs to 2E1C2: %s" % ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x2E1C2, 0)])
    L.append("== 22C62"); dump(0x22C62, 0x22C91)
    L.append("   refs 22C62: %s ; 22C8B-22C91: %s" % (["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(0x22C62, 0)], [("%X" % a, ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0)]) for a in range(0x22C8B, 0x22C91)]))
    L.append("   bytes 22C62: %s" % ida_bytes.get_bytes(0x22C62, 0x30).hex())
    L.append("== 67F59"); dump(0x67F59, 0x67F7B)
    L.append("   refs 67F59/67F77/67F7B: %s" % [["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0)] for a in (0x67F59, 0x67F77, 0x67F78, 0x67F79, 0x67F7B)])
    L.append("== 69705/69720"); dump(0x69705, 0x69740)
    L.append("   refs 69705/69720/69723: %s" % [["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0)] for a in (0x69705, 0x69720, 0x69722, 0x69723)])
    L.append("== 167440"); dump(0x167440, 0x167452)
    L.append("   refs 167440/167449/16744B/167450: %s" % [["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(a, 0)] for a in (0x167440, 0x167449, 0x16744B, 0x167450)])
    L.append("   bytes 167430: %s" % ida_bytes.get_bytes(0x167430, 0x28).hex())
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
