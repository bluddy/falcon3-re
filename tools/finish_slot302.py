"""Finisher for the one .RTLink thunk slot that refused add_func (finding 56).

Slot #302 @ 0x2C969 = `E8 (call sub_2AFBD) | EA 173F:669F (jmp far) | 43 00`.
register_thunk_slots.py tried DELIT_SIMPLE and DELIT_EXPAND over [s, s+8) and
add_func still returned nothing, so this tries a wider/alternative set and logs
exactly what each attempt did. Saves only if the slot ends up as its own 8B or
10B function.

Usage: cmd /c "tools\\run_idat.bat tools\\finish_slot302.py"
"""
import traceback

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi
import idc

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\finish302.log"
S, LIMIT = 0x2C969, 0x2C971

log = []
saved = False

try:
    def state(tag):
        f = ida_funcs.get_func(S)
        log.append("    [%s] bytes=%s get_head=0x%X is_head=%s unknown=%s func=%s"
                   % (tag, (ida_bytes.get_bytes(S, 10) or b"").hex(),
                      ida_bytes.get_item_head(S), ida_bytes.is_head(S),
                      ida_bytes.is_unknown(S),
                      ("%X..%X" % (f.start_ea, f.end_ea)) if f else "NONE"))

    def decode(lo, hi):
        pos = lo
        while pos < hi:
            r = ida_ua.create_insn(pos)
            if not r:
                log.append("      create_insn(0x%X) -> 0" % pos)
                return False
            nxt = ida_bytes.next_head(pos, hi)
            if nxt <= pos:
                break
            pos = nxt
        return True

    f0 = ida_funcs.get_func(S)
    log.append("initial: func=%s" % (("%X..%X" % (f0.start_ea, f0.end_ea)) if f0 else "NONE"))
    state("start")

    if f0 and f0.start_ea == S and (f0.end_ea - S) in (8, 10):
        log.append("already its own function, nothing to do")
    else:
        strategies = [
            ("SIMPLE8 + decode[s,s+8) + add(s,s+8)",
             lambda: (ida_bytes.del_items(S, ida_bytes.DELIT_SIMPLE, 8), decode(S, LIMIT),
                      ida_funcs.add_func(S, LIMIT))),
            ("EXPAND8 + decode[s,s+8) + add(s,s+8)",
             lambda: (ida_bytes.del_items(S, ida_bytes.DELIT_EXPAND, 8), decode(S, LIMIT),
                      ida_funcs.add_func(S, LIMIT))),
            ("EXPAND8 + decode[s,s+10) + add(s,s+10)",
             lambda: (ida_bytes.del_items(S, ida_bytes.DELIT_EXPAND, 8), decode(S, S + 10),
                      ida_funcs.add_func(S, S + 10))),
            ("no del_items: create_insn(s) + add(s,s+8)",
             lambda: (ida_ua.create_insn(S), ida_funcs.add_func(S, LIMIT))),
        ]
        for name, fn in strategies:
            try:
                parts = fn()
                r = parts[-1]
                f = ida_funcs.get_func(S)
                log.append("  %-46s add_func=%s -> %s"
                           % (name, r,
                              ("%X..%X" % (f.start_ea, f.end_ea)) if f else "NONE"))
                if f and f.start_ea == S and (f.end_ea - S) in (8, 10):
                    log.append("    SUCCESS with: %s" % name)
                    ida_name.set_name(S, "sub_%X" % S, ida_name.SN_CHECK)
                    break
            except Exception as e:
                log.append("  %-46s RAISED %s" % (name, e))
        state("end")

    f = ida_funcs.get_func(S)
    if f and f.start_ea == S and (f.end_ea - S) in (8, 10):
        # guard: nothing else lost
        THUNK_LO, STRIDE, N = 0x2BD9D, 10, 303
        bad = 0
        for i in range(N):
            s = THUNK_LO + i * STRIDE
            g = ida_funcs.get_func(s)
            if not g or g.start_ea != s:
                bad += 1
        if bad:
            log.append("GUARD FAILED: %d slots not their own function" % bad)
        else:
            log.append("GUARD PASSED: 303/303")
            ida_loader.save_database(IDB, 0)
            saved = True
            log.append("SAVED")
    else:
        log.append("slot #302 still not registered -- NOT SAVED")
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
