"""
decode_overlays_probe.py  —  test whether ADD_CLEAR can decode and register
the overlay auto-queue functions. Tests 3 R29 entries.
Run: idat -A -S"analysis/s1/decode_overlays_probe.py" analysis/s1/probe_overlays.i64
"""
import idc, ida_funcs, ida_bytes, ida_ua, traceback
from pathlib import Path

LOG = Path("analysis/s1/decode_overlays_probe.log")
log = []

TEST_CASES = [
    # (lo, hi, end_expected) from auto queue probe
    (0x131D5F, 0x132012, 0x132012),  # R29_3335s, 691B, retf
    (0x1326CF, 0x13276D, 0x13276D),  # R29_3335s, 158B, retf
    (0x1390C1, 0x139169, 0x139169),  # R29_39F7s, 168B, retf
]

def descend_simple(seed, lo, hi):
    """Simple descent: clear and decode from seed within [lo, hi)."""
    todo = [seed]
    made = set()
    RETS = {"retn", "retf", "iret", "jmp", "jmpf"}
    while todo:
        ea = todo.pop()
        while lo <= ea < hi:
            if ea in made:
                break
            fl = ida_bytes.get_flags(ea)
            if not (ida_bytes.is_code(fl) and ida_bytes.get_item_head(ea) == ea):
                ida_bytes.del_items(ea, ida_bytes.DELIT_SIMPLE, min(8, hi - ea))
                if ida_ua.create_insn(ea) <= 0:
                    raise RuntimeError("cannot decode 0x%X" % ea)
            made.add(ea)
            m = idc.print_insn_mnem(ea)
            if m in RETS:
                break
            if m.startswith("j") or m.startswith("loop"):
                for x in idc.XrefsFrom(ea, 0):
                    if lo <= x < hi:
                        todo.append(x)
                if m == "jmp":
                    break
            ea += max(ida_bytes.get_item_size(ea), 1)
    return made

try:
    for lo, hi, end_exp in TEST_CASES:
        log.append("Testing 0x%X..0x%X (%dB):" % (lo, hi, hi-lo))
        
        # Check initial state
        f_before = ida_funcs.get_func(lo)
        log.append("  before: %s" % ("fn 0x%X..0x%X" % (f_before.start_ea, f_before.end_ea) if f_before else "no fn"))
        
        # Clear and decode
        ida_bytes.del_items(lo, ida_bytes.DELIT_SIMPLE, hi - lo)
        made = descend_simple(lo, lo, hi)
        log.append("  decoded %d instruction heads" % len(made))
        
        # Add function
        r = ida_funcs.add_func(lo, hi)
        log.append("  add_func result: %s" % r)
        
        f_after = ida_funcs.get_func(lo)
        if f_after and f_after.start_ea == lo:
            log.append("  SUCCESS: fn 0x%X..0x%X" % (f_after.start_ea, f_after.end_ea))
        else:
            log.append("  FAIL: no fn at 0x%X" % lo)

except Exception:
    log.append("ERROR:\n" + traceback.format_exc())

LOG.write_text("\n".join(log))
import idaapi; idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
