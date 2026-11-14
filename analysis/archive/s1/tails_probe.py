"""Read-only (DBFL_KILL on a COPY): items, owners and xrefs around the jmp-reached tails. Output analysis/s1/tails.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\tails.txt"
L = []
def dump(lo, hi):
    a = lo
    while a < hi:
        h = ida_bytes.get_item_head(a); sz = max(ida_bytes.get_item_size(h), 1)
        f = ida_funcs.get_func(h)
        L.append("%X %-14s %-40s %s xr=%s" % (h, ida_bytes.get_bytes(h, min(sz, 7)).hex(), idc.generate_disasm_line(h, 0)[:40],
                 ("F%X" % f.start_ea) if f else "-", ["%X/%d" % (x.frm, x.type) for x in idautils.XrefsTo(h, 0) if x.type != 21][:4]))
        a = h + sz
try:
    import ida_segment
    for a in (0x4334E, 0x42F6A, 0x100C00):
        sg = ida_segment.getseg(a); L.append("seg %X: %s" % (a, (ida_segment.get_segm_name(sg), hex(sg.start_ea), hex(sg.end_ea)) if sg else None))
    for lab, lo, hi in (("100B80", 0x100B80, 0x100CC0), ("4334E", 0x43340, 0x43380), ("42F6A", 0x42F50, 0x42F78)):
        L.append("=== " + lab)
        dump(lo, hi)
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
