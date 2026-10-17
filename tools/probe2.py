"""Read-only: why are slot #053 (0x2BFAF) and slot #302 (0x2C969) special?

0x2BFAF: get_func says it belongs to `start` (0x2B19C..0x2B1E5) although it
         lies far outside that head range -> it is one of `start`'s extra
         chunks.  Is that a real control-flow edge, or an artifact?
0x2C969: an undefined item starts at 0x2C967 and spans into the slot, which
         is why a 8B DELIT_SIMPLE did not clear it and add_func refused.

Output: analysis/ida_falconcd/probe2.log
Usage: cmd /c "tools\\run_idat.bat tools\\probe2.py"
"""
import traceback

import ida_bytes
import ida_funcs
import idaapi
import idautils
import idc

LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\probe2.log"
log = []
try:
    # ---- 0x2BFAF : who points at it, and which chunk owns it ----
    log.append("=== 0x2BFAF (slot #053) ===")
    f = ida_funcs.get_func(0x2BFAF)
    log.append("owner head: %s 0x%X..0x%X" % (idc.get_func_name(f.start_ea),
                                              f.start_ea, f.end_ea))
    try:
        ch = ida_funcs.get_fchunk(0x2BFAF)
        log.append("chunk: %s..%s  (head chunk is %s..%s)"
                   % (hex(ch.start_ea), hex(ch.end_ea), hex(f.start_ea), hex(f.end_ea)))
        log.append("chunk IS the head chunk: %s" % (ch.start_ea == f.start_ea))
    except Exception as e:
        log.append("get_fchunk: %s" % e)
    ct = [hex(x) for x in idautils.CodeRefsTo(0x2BFAF, 0)]
    ct1 = [hex(x) for x in idautils.CodeRefsTo(0x2BFAF, 1)]
    log.append("CodeRefsTo flow=0: %s" % (ct or "none"))
    log.append("CodeRefsTo flow=1: %s" % (ct1 or "none"))
    for x in idautils.CodeRefsTo(0x2BFAF, 1):
        g = ida_funcs.get_func(x)
        log.append("   from 0x%X (in %s)" % (x, idc.get_func_name(g.start_ea) if g else "?"))
    # what are `start`s chunks?
    try:
        pf = ida_funcs.get_func(f.start_ea)
        t = ida_funcs.func_tail_iterator_t(pf)
        t.main()
        while not t.done():
            c = t.tail()
            log.append("   start chunk %s..%s" % (hex(c.start_ea), hex(c.end_ea)))
            t.next()
    except Exception as e:
        log.append("tail iteration: %s" % e)
    # does `start` reach 0x2BFAF by flow?
    sh = ida_funcs.get_func(f.start_ea)
    for h in idautils.Heads(sh.start_ea, sh.end_ea):
        for d in idautils.CodeRefsFrom(h, 1):
            if d == 0x2BFAF:
                log.append("   start flows from 0x%X -> 0x2BFAF" % h)
    log.append("")

    # ---- 0x2C969 : the item that spans it ----
    log.append("=== 0x2C969 (slot #302) ===")
    for ea in (0x2C966, 0x2C967, 0x2C968, 0x2C969, 0x2C96C, 0x2C971):
        log.append("   0x%X is_head=%-5s item_head=0x%X size=%d mnem=%r"
                   % (ea, ida_bytes.is_head(ea), ida_bytes.get_item_head(ea),
                      ida_bytes.get_item_size(ea), idc.print_insn_mnem(ea) or ""))
    log.append("   bytes 0x2C95F..0x2C97B: %s"
               % (ida_bytes.get_bytes(0x2C95F, 0x1C) or b"").hex())
    log.append("   func covering 0x2C967: %s"
               % (lambda g: ("%s 0x%X..0x%X" % (idc.get_func_name(g.start_ea),
                                                g.start_ea, g.end_ea)) if g else "NONE")
               (ida_funcs.get_func(0x2C967)))
    log.append("   func covering 0x2C96C: %s"
               % (lambda g: ("%s 0x%X..0x%X" % (idc.get_func_name(g.start_ea),
                                                g.start_ea, g.end_ea)) if g else "NONE")
               (ida_funcs.get_func(0x2C96C)))
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
