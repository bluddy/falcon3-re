"""Plan probe (COPY, DBFL_KILL): trial linear re-decode of ranges; reports each new insn, the first new head that equals an
ORIGINAL code head ("sync"), and code/jump xrefs that targeted original heads inside the cleared range.
Output: analysis/s1/redecode.txt"""
import traceback
import idaapi, idc, ida_funcs, ida_bytes, ida_ua, idautils
OUT = r"C:\Users\ybarnoy\projects\falcon3\analysis\s1\redecode.txt"
# (label, clear_lo, clear_hi_max)
W = [("106EE2", 0x106EEA, 0x106F00), ("108430", 0x10843C, 0x108450), ("10CE30", 0x10CFA5, 0x10CFC0),
     ("10931E", 0x109388, 0x1093A6), ("109445", 0x109445, 0x109519)]
L = []
try:
    for lab, lo, hi in W:
        orig = set()
        a = lo
        while a < hi:
            h = ida_bytes.get_item_head(a)
            if ida_bytes.is_code(ida_bytes.get_flags(h)):
                orig.add(h)
            a = h + max(ida_bytes.get_item_size(h), 1)
        # xrefs (non-flow) into the cleared range, other than lo
        into = []
        for b in range(lo + 1, hi):
            for x in idautils.XrefsTo(b, 0):
                if x.type != 21 and not (lo <= x.frm < hi):
                    into.append("%X<-%X/%d" % (b, x.frm, x.type))
        ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
        L.append("=== %s clear %X..%X ; orig code heads %d ; xrefs into range (not lo): %s" % (lab, lo, hi, len(orig), into[:8]))
        a, sync = lo, None
        while a < hi:
            n = ida_ua.create_insn(a)
            if n <= 0:
                L.append("  %X: create_insn FAILED bytes=%s" % (a, (ida_bytes.get_bytes(a, 4) or b"").hex()))
                break
            L.append("  %X %-12s %s%s" % (a, ida_bytes.get_bytes(a, n).hex(), idc.generate_disasm_line(a, 0),
                                          "   <== orig head" if a in orig and a != lo else ""))
            a += n
            if a in orig and sync is None:
                sync = a
                L.append("  -- sync at %X (next head is an original head)" % a)
                break
        L.append("")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w").write("\n".join(L))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
