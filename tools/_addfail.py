import traceback
import ida_bytes, ida_funcs, ida_ua, idaapi, idc, ida_segment
ROOT = r"C:\Users\yotam\projects\falcon3"
LOG = ROOT + r"\analysis\ida_falconcd\addfail.log"
log = []
try:
    for ea, end in ((0x4FD48, 0x4FD80), (0x4FD40, 0x4FD48)):
        fl = ida_bytes.get_flags(ea)
        h = ida_bytes.get_item_head(ea)
        raw = idc.get_bytes(ea, 24)
        ins = ida_ua.insn_t()
        n = ida_ua.decode_insn(ins, ea)
        # any existing item crossing ea or end?
        cross = []
        for pos in (ea, end - 1):
            hh = ida_bytes.get_item_head(pos)
            if hh != pos:
                cross.append((pos, hh, ida_bytes.get_item_size(hh),
                              bool(ida_bytes.is_code(ida_bytes.get_flags(hh))),
                              bool(ida_bytes.is_data(ida_bytes.get_flags(hh)))))
        # is there an existing function containing ea?
        f = ida_funcs.get_func(ea)
        g = ida_funcs.get_func(0x4FD40)
        log.append("0x%X..0x%X bytes=%s head=0x%X code=%s data=%s unk=%s fresh=%s/%s "
                   "cross=%s in_fn=%s prev_fn=%s"
                   % (ea, end, raw.hex() if raw else "?", h,
                      bool(ida_bytes.is_code(fl)), bool(ida_bytes.is_data(fl)),
                      bool(ida_bytes.is_unknown(fl)),
                      (ins.get_canon_mnem() or "-") if n else "-", n, cross,
                      ("%X..%X" % (f.start_ea, f.end_ea)) if f else None,
                      ("%X..%X" % (g.start_ea, g.end_ea)) if g else None))
        seg = ida_segment.getseg(ea)
        log.append("   seg=%s perm=%d bitness=%d" % (seg.name if seg else "?",
                                                     seg.perm if seg else -1,
                                                     seg.bitness if seg else -1))
except Exception:
    log.append(traceback.format_exc())
open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)