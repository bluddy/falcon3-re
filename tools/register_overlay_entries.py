"""Register overlay entry points that have no function yet (finding 54).

Candidates come from tools/overlay_entries.json -- file/trace-derived
entry_ea values -- and pass four conditions (all re-checked here, not
trusted from the dry run):

  1. entry_ea has no function
  2. first byte is a known prologue (CODE_START)
  3. a 16-bit decode_insn reaches a standalone C3/CB/CF
  4. that end does not overrun the next registered function

Candidates that nest inside another candidate are dropped (finding 50:
a list is not a diagnosis).

NO auto_wait() (finding 37). Saves only if every planned registration
verifies; otherwise exits without save_database.

Usage: cmd /c "tools\run_idat.bat tools\register_overlay_entries.py"
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
CLS = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\classification.json"
ENT = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\overlay_entries.json"
LOG = r"C:\Users\yotam\projects\falcon3\analysis\ida_falconcd\register_entries.log"

CODE_START = {0x55, 0x56, 0x57, 0x53, 0x51, 0x52, 0x50, 0x1e, 0x06, 0x07,
              0xb8, 0xb9, 0xba, 0xbb, 0xbf, 0xbe, 0x33, 0x2e, 0x3e, 0x8b,
              0x8c, 0x8e, 0xc7, 0x83, 0x81, 0xe8, 0x9a, 0xb4, 0x31, 0xc8, 0x9c}
TERMS = {0xc3, 0xcb, 0xcf}

log = []
ok_all = False

try:
    cls = json.load(open(CLS))
    ent = json.load(open(ENT))
    registered = sorted(i["ea"] for i in cls.values())
    have = {i["ea"] for i in cls.values()}

    def probe(ea, limit):
        ins = ida_ua.insn_t()
        pos = ea
        while pos < limit:
            n = ida_ua.decode_insn(ins, pos)
            if n <= 0:
                return None
            if ida_bytes.get_byte(pos) in TERMS and n == 1:
                return pos + 1
            pos += n
        return None

    cands = []
    for e in ent:
        ea = e["entry_ea"]
        if ea in have:
            continue
        if ida_funcs.get_func(ea):
            continue
        if ida_bytes.get_byte(ea) not in CODE_START:
            continue
        nxt = next((x for x in registered if x > ea), ea + 600)
        limit = min(nxt, ea + 600)
        end = probe(ea, limit)
        if end is None or end > nxt or end - ea < 6:
            continue
        cands.append((ea, end, e.get("seg_name")))

    cands.sort()
    plan = []
    for ea, end, sn in cands:
        if any(not (end <= s2 or ea >= e2) for s2, e2, _ in plan):
            log.append("  0x%X dropped (nested in another candidate)" % ea)
            continue
        plan.append((ea, end, sn))
    log.append("candidates passing all 4 conditions: %d   after nest-drop: %d"
               % (len(cands), len(plan)))

    registered_now = []
    for ea, end, sn in plan:
        ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, 8)
        if not ida_ua.create_insn(ea):
            log.append("  0x%X FAIL create_insn" % ea)
            continue
        ok = ida_funcs.add_func(ea, end)
        if ok:
            ida_funcs.set_func_end(ea, end)
        name = "sub_%X" % ea
        ida_name.set_name(ea, name, ida_name.SN_CHECK)
        f = ida_funcs.get_func(ea)
        got = ("%s-%s" % (hex(f.start_ea), hex(f.end_ea))) if f else "NONE"
        log.append("  0x%X %4dB seg=%-12s add_func=%s -> %s"
                   % (ea, end - ea, sn, ok, got))
        if f and f.start_ea == ea and f.end_ea == end:
            registered_now.append((ea, end, name))

    log.append("verified registrations: %d / %d planned"
               % (len(registered_now), len(plan)))

    problems = []
    if len(registered_now) != len(plan):
        problems.append("%d of %d did not verify"
                        % (len(plan) - len(registered_now), len(plan)))
    starts = [p[0] for p in plan]
    for ea, end, _ in plan:
        f = ida_funcs.get_func(ea)
        if not f or f.start_ea != ea or f.end_ea != end:
            problems.append("0x%X range mismatch" % ea)
            continue
        nxt = next((s for s in starts if s > ea), None)
        if nxt is not None and f.end_ea > nxt:
            problems.append("0x%X overruns next candidate" % ea)
    if problems:
        log.append("GUARD FAILED: %s" % "; ".join(problems[:10]))
        ok_all = False
    else:
        log.append("GUARD PASSED")
        ok_all = True

except Exception:
    log.append("EXCEPTION (db dirty -- restore FALCONCD.EXE.i64.bak_entries):")
    log.append(traceback.format_exc())
    ok_all = False

if ok_all:
    ida_loader.save_database(IDB, 0)
    log.append("SAVED")
else:
    log.append("NOT SAVED -- restore FALCONCD.EXE.i64.bak_entries if it looks wrong")

open(LOG, "w").write("\n".join(log))
idaapi.qexit(0)