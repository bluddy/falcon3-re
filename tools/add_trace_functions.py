"""Register trace-recovered missed functions (finding 37, step 4).

Candidates come from boundary_report.json UNKNOWN targets re-checked against
the comprehensive trace. Naive byte-scanning for c3/cb/cf gives false
positives (c3/cf as 2nd byte of `3b c3`=cmp bx,ax / `3b cf`=cmp cx,di), so
this disassembles instruction-by-instruction and stops only at a ret/retf/
iret sitting on a real instruction boundary.

Skips any candidate whose disassembly runs past the next registered function
(which would mean the candidate is mid-function, not an entry).

Usage: cmd /c "tools\\run_idat.bat tools\\add_trace_functions.py"
"""
import json
import traceback

import ida_bytes
import ida_funcs
import ida_loader
import ida_name
import ida_ua
import idaapi
import idc

IDB = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\FALCONCD.EXE.i64"
REPORT = r"C:\Users\yotam\projects\falcon3\analysis\traces\boundary_report.json"
CLS = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\classification.json"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\addfunc_trace3.log"

THUNK_LO, THUNK_HI = 179613, 182643   # 0x2BD9D..0x2C973 .RTLink thunk table
CODE_START = {0x55, 0x56, 0x57, 0x53, 0x51, 0x52, 0x50, 0x1e, 0x06, 0x07,
              0xb8, 0xb9, 0xba, 0xbb, 0xbf, 0xbe, 0x33, 0x2e, 0x3e, 0x8b,
              0x8c, 0x8e, 0xc7, 0x83, 0x81, 0xe8, 0x9a, 0xb4, 0x31, 0x33}
TERMS = {0xc3: "ret", 0xcb: "retf", 0xcf: "iret"}

log = []
try:
    cls = json.load(open(CLS))
    registered = sorted(i["ea"] for i in cls.values())
    rep = json.load(open(REPORT))

    # collect candidates from UNKNOWN, excluding thunk table + already-in-fn
    cands = []
    for e in rep["unknown"]:
        ea = e["ida_ea"]
        if THUNK_LO <= ea <= THUNK_HI:
            continue
        if any(i["ea"] <= ea < i["ea"] + i["size"] for i in cls.values()):
            continue
        b = ida_bytes.get_byte(ea)
        if b in CODE_START:
            cands.append((e["calls"], ea))
    cands.sort(reverse=True)
    log.append("candidates from UNKNOWN: %d" % len(cands))

    registered_fns = []
    for calls, ea in cands:
        nxt = next((x for x in registered if x > ea), ea + 600)
        limit = min(nxt, ea + 600)

        # Determine the true end by disassembling to a terminator, then
        # register using the PROVEN pattern from apply_trace_functions.py:
        # DELIT_SIMPLE + create_insn(ea) only (first insn), let IDA's
        # autoanalysis decode the body. Pre-decoding the full body with
        # DELIT_EXPAND made auto_wait() re-decide and shrink fns to 1-5B.
        probe_limit = min(limit, ea + 600)
        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, probe_limit - ea)
        pos = ea
        end = None
        fail = None
        while pos < probe_limit:
            if not ida_ua.create_insn(pos):
                fail = pos
                break
            b = ida_bytes.get_byte(pos)
            sz = ida_bytes.get_item_size(pos)
            if sz <= 0:
                fail = pos
                break
            # terminator must be a standalone 1-byte insn on an insn boundary
            if b in TERMS and sz == 1:
                end = pos + 1
                break
            pos += sz

        if fail is not None:
            log.append("  0x%X calls=%d SKIP (decode failed at 0x%X)" % (ea, calls, fail))
            continue
        if end is None:
            log.append("  0x%X calls=%d SKIP (no terminator before 0x%X)" % (ea, calls, probe_limit))
            continue
        if end > nxt:
            log.append("  0x%X calls=%d SKIP (end 0x%X > next_fn 0x%X)" % (ea, calls, end, nxt))
            continue

        size = end - ea
        if size < 6:
            log.append("  0x%X calls=%d SKIP (size %d too small)" % (ea, calls, size))
            continue

        # proven registration: clear first bytes, decode first insn, add_func.
        # If a previous (broken) pass left a 1-5B stub here, delete it first.
        prev = ida_funcs.get_func(ea)
        if prev:
            if prev.start_ea == ea:
                ida_funcs.del_func(ea)
            else:
                log.append("  0x%X SKIP (inside fn 0x%X)" % (ea, prev.start_ea))
                continue
        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, min(end - ea, 8))
        ida_ua.create_insn(ea)
        name = "sub_%X" % ea
        ok = ida_funcs.add_func(ea, end)
        ida_name.set_name(ea, name, ida_name.SN_CHECK)
        f = ida_funcs.get_func(ea)
        got = ("%s-%s" % (hex(f.start_ea), hex(f.end_ea))) if f else "NONE"
        log.append("  0x%X calls=%-7d %dB term=%s add_func=%s -> %s"
                   % (ea, calls, size,
                      TERMS[ida_bytes.get_byte(end - 1)], ok, got))
        if f:
            registered_fns.append((ea, end, name))

    idaapi.auto_wait()
    ida_loader.save_database(IDB, 0)
    log.append("registered %d fns; saved" % len(registered_fns))
except Exception:
    log.append(traceback.format_exc())

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)
