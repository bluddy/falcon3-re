"""Micro-probe: WHY does ida_funcs.add_func(0x2C969, 0x2C971) always fail?

Read-mostly: one create_insn attempt to observe its return value, no save.

Output: analysis/ida_falconcd/probe302.log
Usage: cmd /c "tools\\run_idat.bat tools\\probe302.py"
"""
import traceback

import ida_bytes
import ida_funcs
import idaapi
import ida_ua
import idc

LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\probe302.log"
S = 0x2C969
log = []
try:
    def snap(tag):
        log.append("[%s] unknown=%s is_head=%s head=0x%X size=%d flags=0x%X mnem=%r"
                   % (tag, ida_bytes.is_unknown(S), ida_bytes.is_head(S),
                      ida_bytes.get_item_head(S), ida_bytes.get_item_size(S),
                      ida_bytes.get_flags(S), idc.print_insn_mnem(S) or ""))

    snap("before")
    r = ida_ua.create_insn(S)
    log.append("create_insn(0x%X) returned %r" % (S, r))
    snap("after create_insn")

    for ea in (0x2C967, 0x2C96C, 0x2C971, 0x2C973):
        try:
            ch = ida_funcs.get_fchunk(ea)
            log.append("get_fchunk(0x%X) -> %s" % (
                ea, ("%X..%X owner=?" % (ch.start_ea, ch.end_ea)) if ch else "None"))
        except Exception as e:
            log.append("get_fchunk(0x%X) raised %s" % (ea, e))
except Exception:
    log.append(traceback.format_exc())

try:
    import idautils
    claims = []
    for fea in idautils.Functions(0x2C800, 0x2CA00):
        g = ida_funcs.get_func(fea)
        claims.append("%s %X..%X" % (idc.get_func_name(fea), g.start_ea, g.end_ea))
    log.append("functions 0x2C800..0x2CA00: %s" % "; ".join(claims))

    # what does IDA think the containing function is, exactly?
    g = ida_funcs.get_func(S)
    log.append("get_func(0x%X) -> %s" % (S, ("%X..%X" % (g.start_ea, g.end_ea)) if g else "None"))

    # try add_func and report
    r = ida_funcs.add_func(S, 0x2C971)
    log.append("add_func(0x%X, 0x2C971) returned %r" % (S, r))
    g = ida_funcs.get_func(S)
    log.append("  now get_func -> %s" % (("%X..%X" % (g.start_ea, g.end_ea)) if g else "None"))

    # is the address inside a segment marked CODE?
    import ida_segment
    sg = ida_segment.getseg(S)
    if sg is not None:
        log.append("segment %X..%X class=%s" % (sg.start_ea, sg.end_ea,
                                                ida_segment.get_segm_class(sg)))
    else:
        log.append("NO SEGMENT at 0x%X" % S)
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
