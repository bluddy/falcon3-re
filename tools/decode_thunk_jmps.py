"""Define the missing `JMP FAR` instruction at every thunk slot's +3 (finding 56).

register_thunk_slots.py created the 277 new slot functions but its decode loop
advanced with `next_head(slot, slot+8)` -- after the 3-byte `call` there is no
head yet, so it jumped straight to the limit and never created the 5-byte
`jmp far` at slot+3.  Consequences: `last_insns` recorded `call` instead of
`jmp`, and (the one that matters) `export_callrefs.py` saw no `jmp` mnemonic
there, so the `slot -> overlay` half of Resident -> Thunk -> Overlay was still
not exported.

This walks each slot's code span by instruction SIZE instead, creating whatever
is missing, and refuses to save unless all 303 slots have a real `jmp` at +3.

Function spans are not touched (only instruction items are created), so
`function_bytes.json` is unaffected -> verify_rebuild cannot see churn here.

Usage: cmd /c "tools\\run_idat.bat tools\\decode_thunk_jmps.py"
"""
import traceback

import ida_bytes
import ida_funcs
import ida_loader
import ida_ua
import idaapi
import idc

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\decode_thunks.log"
THUNK_LO, STRIDE, N = 0x2BD9D, 10, 303

log = []
ok_all = False

try:
    created = already = 0
    fails = []
    for i in range(N):
        s = THUNK_LO + i * STRIDE
        f = ida_funcs.get_func(s)
        if not f or f.start_ea != s:
            continue                      # slot #302: blocked by seg021/seg022 boundary
        limit = min(f.end_ea, s + 8)
        pos = s
        guard = 0
        while pos < limit and guard < 16:
            guard += 1
            sz = ida_bytes.get_item_size(pos) if idc.print_insn_mnem(pos) else 0
            if sz > 0:
                pos += sz
                continue
            ida_bytes.del_items(pos, ida_bytes.DELIT_SIMPLE, 1)
            r = ida_ua.create_insn(pos)
            if not r:
                fails.append((s, pos, "create_insn returned 0"))
                break
            created += 1
            pos += r
        m3 = idc.print_insn_mnem(s + 3) or ""
        if m3.startswith("jmp"):
            already += 1
        else:
            fails.append((s, s + 3, "mnem=%r after decode" % m3))

    log.append("slots whose +3 is now `jmp`: %d/%d  (instructions created: %d)"
               % (already, N, created))
    for s, ea, why in fails[:20]:
        log.append("    slot 0x%X @0x%X: %s" % (s, ea, why))

    # guard: spans unchanged AND every registered slot has jmp@+3
    bad = []
    for i in range(N):
        s = THUNK_LO + i * STRIDE
        f = ida_funcs.get_func(s)
        if not f or f.start_ea != s:
            if i != 302:                  # documented exception, see header
                bad.append((s, "not its own function"))
            continue
        if f.end_ea - s not in (8, 10):
            bad.append((s, "span %d" % (f.end_ea - s)))
        if not (idc.print_insn_mnem(s + 3) or "").startswith("jmp"):
            bad.append((s, "no jmp at +3"))
    if bad:
        log.append("GUARD FAILED: %d problems" % len(bad))
        for s, why in bad[:20]:
            log.append("    0x%X: %s" % (s, why))
    else:
        log.append("GUARD PASSED: 302 slots all decode call..jmp (slot #302 excluded)")
        ok_all = True

    if ok_all:
        ida_loader.save_database(IDB, 0)
        log.append("SAVED")
    else:
        log.append("NOT SAVED")
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
