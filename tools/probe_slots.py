"""Read-only probe: why did slot #053 (0x2BFAF) and slot #302 (0x2C969)
fail in register_thunk_slots.py?

Output: analysis/ida_falconcd/probe_slots.log
Usage: cmd /c "tools\\run_idat.bat tools\\probe_slots.py"
"""
import traceback

import ida_bytes
import ida_funcs
import idaapi
import idautils
import idc

LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\probe_slots.log"
log = []
try:
    for ea in (0x2BFAF, 0x2C969, 0x2BFA7, 0x2C961, 0x2C971):
        f = ida_funcs.get_func(ea)
        flags = ("%X" % f.flags) if f else "-"
        tail = bool(f and (f.flags & ida_funcs.FUNC_TAIL))
        log.append("0x%X  bytes=%s" % (ea, (ida_bytes.get_bytes(ea, 12) or b"").hex()))
        log.append("    get_func -> %s" % (
            ("%s 0x%X..0x%X flags=%s TAIL=%s" % (idc.get_func_name(f.start_ea),
                                                  f.start_ea, f.end_ea, flags, tail))
            if f else "NONE"))
        h = ida_bytes.get_item_head(ea)
        log.append("    item_head=0x%X  is_head=%s  mnem=%r  item_size=%d"
                   % (h, ida_bytes.is_head(ea), idc.print_insn_mnem(ea) or "",
                      ida_bytes.get_item_size(ea)))
        # every function whose range is anywhere near
        near = []
        for fea in idautils.Functions(ea - 0x60, ea + 0x60):
            g = ida_funcs.get_func(fea)
            near.append("%s 0x%X..0x%X%s" % (idc.get_func_name(fea), g.start_ea,
                                             g.end_ea,
                                             " TAIL" if g.flags & ida_funcs.FUNC_TAIL else ""))
        log.append("    functions within +-0x60: %s" % ("; ".join(near) or "none"))
        # does this ea belong to a chunk of another func? (tail check via get_func on head)
        if f is not None and f.start_ea != ea:
            log.append("    ** NOT the function start: it belongs to %s **"
                       % idc.get_func_name(f.start_ea))
        log.append("")

    # how many of the 303 slots are tails / not-starts right now?
    THUNK_LO, STRIDE, N = 0x2BD9D, 10, 303
    own = tailn = other = none = 0
    others = []
    for i in range(N):
        s = THUNK_LO + i * STRIDE
        f = ida_funcs.get_func(s)
        if f is None:
            none += 1
        elif f.start_ea == s:
            own += 1
        elif f.flags & ida_funcs.FUNC_TAIL:
            tailn += 1
            others.append((s, f.start_ea, idc.get_func_name(f.start_ea)))
        else:
            other += 1
            others.append((s, f.start_ea, idc.get_func_name(f.start_ea)))
    log.append("slot status NOW: own-function=%d  TAIL-of-another=%d  "
               "inside-other=%d  none=%d" % (own, tailn, other, none))
    for s, st, nm in others[:30]:
        log.append("    slot 0x%X is %s of 0x%X (%s)" % (s, "TAIL" if True else "",
                                                         st, nm))
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
