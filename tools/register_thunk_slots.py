"""Register all 303 .RTLink thunk slots as their own functions (finding 56).

Every slot at 0x2BD9D + i*10 is a 10-byte stub: `E8 disp16` (call the RTLink
loader) + `EA off seg` (JMP FAR to the overlay entry) + a rec_id word.

Why this is needed (finding 55):
  * `export_callrefs.py` walks heads *inside functions only*, so 254 slots
    emitted no ref at all -> 228 refs INTO the table left 204 unresolved, and
    the `slot -> overlay` half of Resident -> Thunk -> Overlay was never exported.
  * 2 slots are swallowed by `sub_2BE83` (20B) and 21 by
    `sub_2BFCD` / `overlay_tail_bridge_b` (210B): IDA merged them because decode
    stops at the JMP FAR, so their inner `slot+3` never became a `jmp` head.
  * slot #053 (0x2BFAF) sits in a foreign chunk owned by `start` -- `start`
    really does transfer control there, so the xref stays; only the chunk
    ownership moves (remove_func_tail), which is what lets the slot be its own
    function and keeps the edge as `start -> slot -> overlay`.

Sizes: free slots are **8B** (E8 + EA), matching the 26 already correct -- the
rec_id word is data, not code.  The two split ranges must **tile their original
span exactly** or `verify_rebuild` reports CHANGED instead of SPLIT, so their
pieces are **10B** (E8 + EA + rec_id), with the rec word left undecoded so
`export_epilogues` still records `last_mnem = jmp`.

Guarded: exits WITHOUT saving unless all 303 slots are their own function.
No auto_wait (finding 37).  Note idat may persist a dirty DB anyway, so if the
guard fails restore `FALCONCD.EXE.i64.bak_thunk303`.

Usage: cmd /c "tools\\run_idat.bat tools\\register_thunk_slots.py"
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
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\register_thunks.log"
THUNK_LO, STRIDE, N = 0x2BD9D, 10, 303

log = []
ok_all = False

try:
    slots = [THUNK_LO + i * STRIDE for i in range(N)]
    slot_set = set(slots)

    def code_part(slot, limit):
        """Decode [slot, limit) instruction by instruction; leave trailing data."""
        pos = slot
        while pos < limit:
            if not ida_ua.create_insn(pos):
                log.append("    0x%X create_insn FAILED" % pos)
                return False
            nxt = ida_bytes.next_head(pos, limit)
            if nxt <= pos:
                break
            pos = nxt
        return True

    # ---- 1. classify the table ----
    free, good, owners, foreign = [], [], {}, []
    for s in slots:
        f = ida_funcs.get_func(s)
        if f is None:
            free.append(s)
        elif f.start_ea == s:
            sz = f.end_ea - s
            if sz in (8, 10):
                good.append(s)
            else:
                owners[s] = f.end_ea
        elif f.start_ea in slot_set and (f.end_ea - f.start_ea) % STRIDE == 0:
            owners.setdefault(f.start_ea, f.end_ea)   # interior of a thunk run
        else:
            foreign.append((s, f))                     # chunk owned elsewhere

    log.append("table: %d slots | already correct: %d | free: %d | merged runs: %d "
               "| foreign-owned: %d"
               % (N, len(good), len(free), len(owners), len(foreign)))

    # ---- 1b. detach foreign chunks (xrefs stay; only ownership moves) ----
    for s, f in foreign:
        nm = idc.get_func_name(f.start_ea)
        log.append("  slot 0x%X owned by chunk of %s (0x%X..0x%X) -> remove_func_tail"
                   % (s, nm, f.start_ea, f.end_ea))
        try:
            got = ida_funcs.remove_func_tail(f, s)
        except Exception as e:
            got = False
            log.append("    remove_func_tail raised: %s" % e)
        g = ida_funcs.get_func(s)
        if got and g is None:
            free.append(s)
            log.append("    detached -> now free")
        else:
            log.append("    detach FAILED (still %s)"
                       % (("%s 0x%X" % (idc.get_func_name(g.start_ea), g.start_ea))
                          if g else "got=%s" % got))

    # ---- 2. split the merged ranges ----
    split_slots = set()
    for start in sorted(owners):
        end = owners[start]
        if (start - THUNK_LO) % STRIDE or (end - start) % STRIDE:
            log.append("  REFUSING to split 0x%X..0x%X (not slot-aligned)"
                       % (start, end))
            continue
        nslot = (end - start) // STRIDE
        wanted = {}
        for i in range(nslot):
            s = start + i * STRIDE
            nm = ida_name.get_ea_name(s) or ""
            if nm.startswith(("unk_", "byte_", "word_", "dword_", "qword_",
                              "off_", "asc_", "str_")):
                nm = ""
            wanted[s] = nm if nm else ("sub_%X" % s)
        if not ida_funcs.del_func(start):
            log.append("  0x%X del_func FAILED" % start)
            continue
        ida_bytes.del_items(start, ida_bytes.DELIT_EXPAND, end - start)
        ok = 0
        for i in range(nslot):
            s = start + i * STRIDE
            if not code_part(s, s + 8):
                log.append("    0x%X decode failed, abort range" % s)
                break
            r = ida_funcs.add_func(s, s + STRIDE)
            ida_name.set_name(s, wanted[s], ida_name.SN_CHECK)
            f = ida_funcs.get_func(s)
            if r and f and f.start_ea == s and f.end_ea - s == STRIDE:
                ok += 1
                split_slots.add(s)
            else:
                log.append("    0x%X add_func(%d B) did not verify -> %s"
                           % (s, STRIDE,
                              ("%X..%X" % (f.start_ea, f.end_ea)) if f else "NONE"))
                break
        log.append("  split 0x%X..0x%X: %d/%d slots registered" % (start, end, ok, nslot))

    # ---- 3. register the free slots (8B: E8 + EA, rec word stays data) ----
    got = 0
    for s in free:
        done = False
        # DELIT_SIMPLE first; fall back to DELIT_EXPAND for slots whose item
        # starts BEFORE the slot (slot #302: an 8B undefined item begins at
        # 0x2C967, so a SIMPLE delete inside [s, s+8) left it broken and
        # add_func refused).
        for dflag, dname in ((ida_bytes.DELIT_SIMPLE, "SIMPLE"),
                             (ida_bytes.DELIT_EXPAND, "EXPAND")):
            ida_bytes.del_items(s, dflag, 8)
            if not code_part(s, s + 8):
                continue
            ida_funcs.add_func(s, s + 8)
            f = ida_funcs.get_func(s)
            if f and f.start_ea == s and f.end_ea - s == 8:
                ida_name.set_name(s, "sub_%X" % s, ida_name.SN_CHECK)
                done = True
                log.append("  0x%X registered 8B (del_items=%s)" % (s, dname))
                break
        if done:
            got += 1
        else:
            f = ida_funcs.get_func(s)
            log.append("    0x%X add_func FAILED -> %s"
                       % (s, ("%X..%X" % (f.start_ea, f.end_ea)) if f else "NONE"))
    log.append("free slots registered: %d/%d" % (got, len(free)))

    # ---- 4. guard ----
    bad = []
    for s in slots:
        f = ida_funcs.get_func(s)
        if not f or f.start_ea != s:
            bad.append((s, ("%X..%X" % (f.start_ea, f.end_ea)) if f else "NONE",
                        "not its own function"))
            continue
        sz = f.end_ea - s
        if s in split_slots and sz != STRIDE:
            bad.append((s, "%X..%X" % (f.start_ea, f.end_ea),
                        "split piece is %dB, need %dB" % (sz, STRIDE)))
        elif s not in split_slots and sz not in (8, 10):
            bad.append((s, "%X..%X" % (f.start_ea, f.end_ea), "size %d" % sz))
    if bad:
        log.append("GUARD FAILED: %d problems" % len(bad))
        for s, rng, why in bad[:30]:
            log.append("    0x%X -> %s : %s" % (s, rng, why))
    else:
        log.append("GUARD PASSED: all %d slots are their own function" % N)
        ok_all = True

    if ok_all:
        ida_loader.save_database(IDB, 0)
        log.append("SAVED")
    else:
        log.append("NOT SAVED -- restore FALCONCD.EXE.i64.bak_thunk303 if needed")
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
