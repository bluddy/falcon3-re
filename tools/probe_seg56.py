"""Finding 56 step 4 (read-only): is there a secondary header or a segment
split inside R05_1E10 at +0x1540 (= 0x0154 paragraphs, IDA 0x2E100+0x1540 =
0x2F640), or is that offset purely the paragraph anchor carried in the fixup
pair's `seg` field?

Output: analysis/ida_falconcd/seg56.log
Usage: cmd /c "tools\\run_idat.bat tools\\probe_seg56.py"
"""
import traceback

import ida_bytes
import ida_funcs
import ida_segment
import idaapi
import idautils
import idc

LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\seg56.log"
BASE, DELTA = 0x2E100, 0x1540
AT = BASE + DELTA          # 0x2F640
log = []
try:
    def seginfo(ea):
        s = ida_segment.getseg(ea)
        if s is None:
            return "NO SEGMENT"
        return "%s 0x%X..0x%X class=%r bitness=%d" % (
            ida_segment.get_segm_name(s), s.start_ea, s.end_ea,
            ida_segment.get_segm_class(s), s.bitness)

    log.append("record base  : 0x%X -> %s" % (BASE, seginfo(BASE)))
    log.append("base+0x1540  : 0x%X -> %s" % (AT, seginfo(AT)))
    log.append("same segment? %s   (a split would show two segments here)"
               % (ida_segment.getseg(BASE) is ida_segment.getseg(AT)))

    log.append("")
    log.append("0x%X : is_head=%s item_head=0x%X mnem=%r item_size=%d unknown=%s"
               % (AT, ida_bytes.is_head(AT), ida_bytes.get_item_head(AT),
                  idc.print_insn_mnem(AT) or "", ida_bytes.get_item_size(AT),
                  ida_bytes.is_unknown(AT)))
    log.append("     bytes@AT-8..AT+16: %s" % (ida_bytes.get_bytes(AT - 8, 24) or b"").hex())
    f = ida_funcs.get_func(AT)
    log.append("     function covering AT: %s" % (
        ("%s 0x%X..0x%X (%dB)" % (idc.get_func_name(f.start_ea), f.start_ea,
                                  f.end_ea, f.end_ea - f.start_ea)) if f else "NONE"))

    # any function START near the boundary? a header would show as a start/gap
    near = [(fea, idc.get_func_name(fea)) for fea in idautils.Functions(AT - 0x80, AT + 0x80)]
    log.append("     function starts within +-0x80: %s"
               % ("; ".join("%s@0x%X" % (n, e) for e, n in near) or "none"))

    # is there any comment / extra item marking a boundary?
    cmt = ida_bytes.get_cmt(AT, 0) or ida_bytes.get_cmt(AT, 1) or ""
    log.append("     comment at AT: %r" % cmt)

    # does the boundary coincide with an ida_segment start anywhere nearby?
    log.append("")
    log.append("segments overlapping 0x2E000..0x31000:")
    for i in range(ida_segment.get_segm_qty()):
        s = ida_segment.getnseg(i)
        if s.start_ea < 0x31000 and s.end_ea > 0x2E000:
            log.append("   %-12s 0x%X..0x%X" % (ida_segment.get_segm_name(s),
                                                s.start_ea, s.end_ea))
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
