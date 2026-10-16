"""Register the two genuine missed functions found via indirect_far targets.

Leads from callgraph analysis (finding 38):
  0x17263  22,178 indirect-far CALLs from 0883:0483 (VGA/port routine)
  0x286CE  2,106 indirect-far CALLs from main hub 1161:1EDC

Boundary = first standalone ret/retf/iret on a real instruction boundary,
clipped so we never cross the next registered function.

Registration uses the fix_trace_functions.py proven pattern: disable
autoanalysis, force-decode the whole range, set_func_end, save WITHOUT
auto_wait (auto_wait shrank previously-registered fns, finding 37).

Usage: cmd /c "tools\\run_idat.bat tools\\add_indirect_targets.py"
"""
import traceback

import ida_auto
import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi
import idautils
import idc

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\addfunc_indirect.log"

CANDIDATES = [0x17263, 0x286CE]
TERMS = {0xC3: "ret", 0xCB: "retf", 0xCF: "iret"}

log = []
try:
    starts = sorted(idautils.Functions())

    # pass 1: find boundaries (probe decode)
    plan = []
    for ea in CANDIDATES:
        nxt = next((s for s in starts if s > ea), ea + 600)
        limit = min(nxt, ea + 600)
        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, limit - ea)
        pos = ea
        end = None
        fail = None
        while pos < limit:
            if not ida_ua.create_insn(pos):
                # a defined data item (e.g. cs-relative var like word_28759)
                # can block code creation at a code/data overlap; force-clear
                # it with DELIT_EXPAND and retry once.
                ida_bytes.del_items(pos, ida_bytes.DELIT_EXPAND, 16)
                if not ida_ua.create_insn(pos):
                    fail = pos
                    break
            b = ida_bytes.get_byte(pos)
            sz = ida_bytes.get_item_size(pos)
            if sz <= 0:
                fail = pos
                break
            if b in TERMS and sz == 1:
                end = pos + 1
                break
            pos += sz
        if end is None:
            log.append("0x%X SKIP: no terminator (fail=%s limit=0x%X)"
                       % (ea, hex(fail) if fail else "-", limit))
            continue
        if end > nxt:
            log.append("0x%X SKIP: end 0x%X > next_fn 0x%X" % (ea, end, nxt))
            continue
        plan.append((ea, end))
        log.append("0x%X -> end 0x%X (%dB) term=%s" %
                   (ea, end, end - ea, TERMS[ida_bytes.get_byte(end - 1)]))

    # pass 2: register with autoanalysis disabled
    ida_auto.enable_auto(False)
    for ea, end in plan:
        prev = ida_funcs.get_func(ea)
        if prev and prev.start_ea == ea:
            ida_funcs.del_func(ea)
        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, end - ea)
        pos = ea
        bad = None
        while pos < end:
            if not ida_ua.create_insn(pos):
                ida_bytes.del_items(pos, ida_bytes.DELIT_EXPAND, 16)
                if not ida_ua.create_insn(pos):
                    bad = pos
                    break
            sz = ida_bytes.get_item_size(pos)
            if sz <= 0:
                bad = pos
                break
            pos += sz
        if bad is not None or pos != end:
            log.append("0x%X re-decode mismatch bad=%s pos=0x%X -> ABORT"
                       % (ea, hex(bad) if bad else "-", pos))
            continue
        ok = ida_funcs.add_func(ea, end)
        ida_name.set_name(ea, "sub_%X" % ea, ida_name.SN_CHECK)
        if ok:
            ida_funcs.set_func_end(ea, end)
        f = ida_funcs.get_func(ea)
        log.append("  add_func=%s -> %s" %
                   (ok, ("%s-%s" % (hex(f.start_ea), hex(f.end_ea))) if f else "NONE"))

    ida_loader.save_database(IDB, 0)
    ida_auto.enable_auto(True)
    log.append("saved (no auto_wait); total fns=%d" % len(list(idautils.Functions())))
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
