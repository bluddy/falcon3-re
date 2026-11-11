"""
segclip_probe.py  —  test splitting segment_clip_test at 0x26099
by removing the tail chunk first, splitting, then re-attaching the tail.
Run on a PROBE COPY: idat -A -S"analysis/s1/segclip_probe.py" analysis/s1/probe_segclip.i64
"""
import idc, ida_funcs, ida_bytes, traceback
from pathlib import Path

LOG = Path("analysis/s1/segclip_probe.log")
log = []

try:
    OWNER = 0x25F93
    AT    = 0x26099
    TAIL_START = 0x25F8F
    TAIL_END   = 0x25F93

    f = ida_funcs.get_func(OWNER)
    log.append("Before: owner=0x%X end=0x%X" % (f.start_ea, f.end_ea))
    
    # List tail chunks
    ci = ida_funcs.func_tail_iterator_t(f)
    tails = []
    ok = ci.main()
    while ok:
        c = ci.chunk()
        tails.append((c.start_ea, c.end_ea))
        ok = ci.next()
    log.append("Tails: %s" % tails)
    
    END = f.end_ea  # 0x260A9 — save before set_func_end changes it
    
    # Try direct set_func_end (bypassing del_func)
    # This might work even with tail chunks — the tail stays with the stub
    r_sfe = ida_funcs.set_func_end(OWNER, AT)
    log.append("set_func_end(0x%X, 0x%X): %s" % (OWNER, AT, r_sfe))
    
    f_after = ida_funcs.get_func(OWNER)
    if f_after:
        ci_a = ida_funcs.func_tail_iterator_t(f_after)
        tails_a = []
        ok = ci_a.main()
        while ok:
            c = ci_a.chunk()
            tails_a.append((hex(c.start_ea), hex(c.end_ea)))
            ok = ci_a.next()
        log.append("stub after sfe: end=0x%X tails=%s" % (f_after.end_ea, tails_a))
    
    # Add second function
    r_af = ida_funcs.add_func(AT, END)
    log.append("add_func(0x%X, 0x%X): %s" % (AT, END, r_af))
    
    f_new = ida_funcs.get_func(AT)
    log.append("New fn: exists=%s end=%s" % (
        f_new is not None and f_new.start_ea == AT,
        hex(f_new.end_ea) if f_new else "N/A"))
    
    # Step 2: add the stub (without tail - IDA may add tail back automatically or not)
    r_add1 = ida_funcs.add_func(OWNER, AT)
    log.append("add_func stub(0x%X, 0x%X): %s" % (OWNER, AT, r_add1))
    
    # Check if tail was auto-added
    f2 = ida_funcs.get_func(OWNER)
    if f2:
        ci2 = ida_funcs.func_tail_iterator_t(f2)
        tails2 = []
        ok = ci2.main()
        while ok:
            c = ci2.chunk()
            tails2.append((c.start_ea, c.end_ea))
            ok = ci2.next()
        log.append("stub after add: end=0x%X tails=%s" % (f2.end_ea, tails2))
    
    # Step 3: add the second function
    r_add2 = ida_funcs.add_func(AT, END)
    log.append("add_func new(0x%X, 0x%X): %s" % (AT, END, r_add2))
    
    # Step 4: re-attach tail to stub if not already there
    f_stub = ida_funcs.get_func(OWNER)
    ci3 = ida_funcs.func_tail_iterator_t(f_stub)
    has_tail = any(c.start_ea == TAIL_START for ok2 in [ci3.main()] for c in [ci3.chunk()] if ok2)
    # Rebuild to check properly
    tails3 = []
    ci4 = ida_funcs.func_tail_iterator_t(f_stub)
    ok = ci4.main()
    while ok:
        c = ci4.chunk()
        tails3.append((c.start_ea, c.end_ea))
        ok = ci4.next()
    log.append("stub tails: %s" % tails3)
    
    if not any(t[0] == TAIL_START for t in tails3):
        r3 = ida_funcs.append_func_tail(f_stub, TAIL_START, TAIL_END)
        log.append("append_func_tail: %s" % r3)
        ci5 = ida_funcs.func_tail_iterator_t(ida_funcs.get_func(OWNER))
        tails4 = []
        ok = ci5.main()
        while ok:
            c = ci5.chunk()
            tails4.append((c.start_ea, c.end_ea))
            ok = ci5.next()
        log.append("after append: %s" % tails4)
    
    # Verify
    f_new = ida_funcs.get_func(AT)
    log.append("New fn: exists=%s" % (f_new is not None and f_new.start_ea == AT))

except Exception:
    log.append("EXCEPTION: " + traceback.format_exc())

LOG.write_text("\n".join(log))
ida_loader = __import__("ida_loader")
ida_loader.set_database_flag(ida_loader.DBFL_KILL)
idc.qexit(0)
