"""
shared_tail_check.py  —  verify owner ea / tail chunks for shared-tail candidates.
Run: idat -A -S"analysis/s1/shared_tail_check.py" analysis/s1/probe_p4b.i64
"""
import idc, ida_funcs, idautils, idc
from pathlib import Path

CANDIDATES = [
    # (at_ea, owner_name from probe)
    (0x26099,  "segment_clip_test"),   # tails=True — investigate
    (0x32D22,  "mode_session_state_reset"),  # jnz from 0x32CD4
    (0x33074,  "mode_session_state_reset"),  # jz from 0x33071 — same owner, chain
    (0x3396E,  "sub_3352A"),
    (0x3B5DB,  "sub_3B5D1"),           # jz from 0x3B5D7
    (0x3B5E9,  "sub_3B5D1"),           # jmp from 0x3B5D9 — same owner, chain
    (0x3B645,  "sub_3B618"),
    (0x41167,  "sub_4113C"),           # mnem=''
    (0x475A1,  "sub_4751E"),           # loop × 2
    (0x4760F,  "sub_4751E"),           # loop × 2 — same owner, chain
    (0x49078,  "sub_48F99"),
    (0x4F0CB,  "sub_4F0B6"),
    (0x6940B,  "ui_loadout_menu_enter"), # P5 deferred
    (0x6D4FC,  "r06_mode_gate_49a3"),
]

def chunks(ea):
    f = ida_funcs.get_func(ea)
    if f is None: return None
    ci = ida_funcs.func_tail_iterator_t(f)
    r = []
    ok = ci.main()
    while ok:
        c = ci.chunk()
        r.append([c.start_ea, c.end_ea])
        ok = ci.next()
    return r

LOG = Path("analysis/s1/shared_tail_check.log")
log = []

for at, hint in CANDIDATES:
    f = ida_funcs.get_func(at)
    if f is None:
        log.append("0x%X (%s): no function" % (at, hint))
        continue
    owner_ea = f.start_ea
    cs = chunks(owner_ea)
    has_tails = cs and cs != [[owner_ea, f.end_ea]]
    mnem = idc.print_insn_mnem(at)
    log.append("0x%X (%s): owner=0x%X end=0x%X tails=%s mnem=%r" % (
        at, hint, owner_ea, f.end_ea, has_tails, mnem))

LOG.write_text("\n".join(log))
import idaapi; idaapi.qexit(0)
