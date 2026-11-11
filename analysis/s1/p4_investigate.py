"""
p4_investigate.py  —  investigate segment_clip_test, 0x41167, and 'other' real targets.
Run: idat -A -S"analysis/s1/p4_investigate.py" analysis/ida_falconcd/FALCONCD.EXE.i64
"""
import idc, ida_funcs, ida_bytes, idautils, idaapi
from pathlib import Path

LOG = Path("analysis/s1/p4_investigate.log")
log = []

def hexbytes(ea, n=16):
    return ' '.join('%02X' % ida_bytes.get_byte(ea+i) for i in range(n))

def prev_insn(ea, fn_start):
    p = idc.prev_head(ea, fn_start)
    if p == idaapi.BADADDR: return None, None
    return p, idc.print_insn_mnem(p)

def chunks(ea):
    f = ida_funcs.get_func(ea)
    if f is None: return []
    ci = ida_funcs.func_tail_iterator_t(f)
    r = []
    ok = ci.main()
    while ok:
        c = ci.chunk()
        r.append((c.start_ea, c.end_ea))
        ok = ci.next()
    return r

# --- 1. segment_clip_test (0x25F93) tail chunks ---
log.append("=== segment_clip_test (0x25F93) ===")
f = ida_funcs.get_func(0x25F93)
if f:
    cs = chunks(0x25F93)
    log.append("  owner end: 0x%X, chunks: %s" % (f.end_ea, cs))
    # What's at 0x26099?
    log.append("  0x26099 bytes: %s" % hexbytes(0x26099))
    log.append("  0x26099 mnem: %r" % idc.print_insn_mnem(0x26099))
    p, pm = prev_insn(0x26099, 0x25F93)
    log.append("  prev at 0x%X: %r" % (p or 0, pm))
    # What are the tail chunks?
    for i, (cs_start, cs_end) in enumerate(cs):
        log.append("  chunk[%d]: 0x%X..0x%X (%d B)" % (i, cs_start, cs_end, cs_end-cs_start))
        log.append("    first insn: %r" % idc.print_insn_mnem(cs_start))
        log.append("    bytes: %s" % hexbytes(cs_start))

# --- 2. 0x41167 (sub_4113C) investigation ---
log.append("")
log.append("=== sub_4113C at 0x41167 ===")
f2 = ida_funcs.get_func(0x4113C)
if f2:
    log.append("  owner: 0x%X..0x%X" % (f2.start_ea, f2.end_ea))
    # Get flags of 0x41167
    fl = ida_bytes.get_flags(0x41167)
    log.append("  flags at 0x41167: 0x%X, is_code=%s, item_head=%X" % (
        fl, ida_bytes.is_code(fl), ida_bytes.get_item_head(0x41167)))
    log.append("  bytes at 0x41167: %s" % hexbytes(0x41167))
    # What instruction is at 0x41162 (5 bytes before)?
    for probe_ea in [0x41160, 0x41162, 0x41163, 0x41164, 0x41165, 0x41166, 0x41167]:
        fl2 = ida_bytes.get_flags(probe_ea)
        head = ida_bytes.get_item_head(probe_ea)
        isz = ida_bytes.get_item_size(head) if ida_bytes.is_code(fl2) else 0
        mnem = idc.print_insn_mnem(probe_ea) if head == probe_ea else ""
        log.append("  0x%X: head=0x%X isz=%d mnem=%r bytes=%s" % (
            probe_ea, head, isz, mnem, hexbytes(probe_ea, 4)))

# --- 3. 'other' real targets investigation ---
OTHER_REAL = [
    (0x11A7D, "cb_args_invoke",          0x11A5E),
    (0x14BE0, "farobj_pos_wrap_update",  None),
    (0x24E46, "sub_24DEC",               0x24DEC),
    (0x4FD52, "hw_state_partial_4fd",    0x4FD4A),
    (0x6E052, "farptr_proc_6e02a",       None),
]
log.append("")
log.append("=== OTHER real targets ===")
for at, hint, owner_hint in OTHER_REAL:
    f3 = ida_funcs.get_func(at)
    if f3 is None:
        log.append("  0x%X (%s): no function!" % (at, hint))
        continue
    owner = f3.start_ea
    fl = ida_bytes.get_flags(at)
    head = ida_bytes.get_item_head(at)
    mnem = idc.print_insn_mnem(at)
    p, pm = prev_insn(at, owner)
    # check for internal xrefs
    inner = []
    for xr in idautils.XrefsTo(at, 0):
        if not xr.iscode: continue
        xf = ida_funcs.get_func(xr.frm)
        if xf and xf.start_ea == owner:
            inner.append((hex(xr.frm), idc.print_insn_mnem(xr.frm)))
    log.append("  0x%X (%s): owner=0x%X end=0x%X head=%X mnem=%r prev=0x%X(%r) inner=%s" % (
        at, hint, owner, f3.end_ea, head, mnem, p or 0, pm, inner))
    log.append("    bytes: %s" % hexbytes(at))
    log.append("    prev bytes: %s" % (hexbytes(p) if p else "none"))

LOG.write_text("\n".join(log))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
