"""
p4_owners.py  —  find owner_ea for terrain_vm_flag_gate and check tail chunks
for the pure-split candidates.
Run: idat -A -S"analysis/s1/p4_owners.py" analysis/s1/probe_p4.i64
"""
import idc, ida_funcs
from pathlib import Path

CANDIDATES = [
    0x26099,   # segment_clip_test
    0x3FB08,   # sub_3FAAE
    0x41167,   # sub_4113C
    0x4F870,   # sub_4F84B
    0x4F964,   # terrain_vm_flag_gate
    0x6E404,   # r14_farptr_call_gate
    0x6E43B,   # r14_farptr_call_gate
    0x12C764,  # sub_12C683
]

LOG = Path("analysis/s1/p4_owners.log")
log = []

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

for t in CANDIDATES:
    f = ida_funcs.get_func(t)
    if f is None:
        log.append("0x%X: no function" % t)
        continue
    owner_ea = f.start_ea
    owner_name = idc.get_func_name(owner_ea)
    cs = chunks(owner_ea)
    has_tails = cs and cs != [[owner_ea, f.end_ea]]
    mnem_at_t = idc.print_insn_mnem(t)
    log.append("0x%X: owner=0x%X (%s) end=0x%X tails=%s mnem=%r" % (
        t, owner_ea, owner_name, f.end_ea, has_tails, mnem_at_t))

LOG.write_text("\n".join(log))
import idaapi; idaapi.qexit(0)
