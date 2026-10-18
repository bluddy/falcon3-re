import traceback
import ida_bytes, ida_funcs, ida_ua, idaapi, idc, idautils
ROOT = r"C:\Users\yotam\projects\falcon3"
LOG = ROOT + r"\analysis\ida_falconcd\addfail.log"
log = []
try:
    for ea in (0x4FD48, 0x4FD38, 0x4FD20, 0x4FD80):
        fl = ida_bytes.get_flags(ea)
        log.append("0x%X code=%s data=%s unk=%s size=%d head=0x%X name=%s"
                   % (ea, bool(ida_bytes.is_code(fl)), bool(ida_bytes.is_data(fl)),
                      bool(ida_bytes.is_unknown(fl)), ida_bytes.get_item_size(ea),
                      ida_bytes.get_item_head(ea), idc.get_name(ea) or "-"))
    h = ida_bytes.get_item_head(0x4FD48)
    n = ida_bytes.get_item_size(h)
    log.append("item @0x%X size=%d bytes=%s" % (h, n, (idc.get_bytes(h, n) or b"").hex()))
    # decode_at reproduction
    ea = 0x4FD48
    hh = ida_bytes.get_item_head(ea); fl = ida_bytes.get_flags(ea)
    if hh == ea and ida_bytes.is_code(fl):
        src = "ida-code"
    elif hh == ea and ida_bytes.is_data(fl):
        src = "DATA"
    else:
        ins = ida_ua.insn_t(); k = ida_ua.decode_insn(ins, ea)
        src = "fresh/%d" % k
    log.append("decode_at(0x4FD48) -> %s (head==ea=%s)" % (src, hh == ea))
    # add_func dry: why did it fail? try add_func on a copy? No -- read func state
    log.append("get_func(0x4FD48)=%s get_func(0x4FD80)=%s"
               % (ida_funcs.get_func(0x4FD48), ida_funcs.get_func(0x4FD80)))
    # existing chunk flags
    f = ida_funcs.get_func(0x4FD38)
    if f:
        log.append("prev fn 0x%X..0x%X flags=%X" % (f.start_ea, f.end_ea, f.flags))
    # is 0x4FD48..0x4FD80 an existing data item (would block add_func)?
    log.append("is_head(0x4FD48)=%s is_data(0x4FD48)=%s"
               % (bool(ida_bytes.is_head(ida_bytes.get_flags(0x4FD48))),
                  bool(ida_bytes.is_data(ida_bytes.get_flags(0x4FD48)))))
except Exception:
    log.append(traceback.format_exc())
open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)