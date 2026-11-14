"""p5_bytes_probe.py — examine key byte positions in the P5 cluster."""
import idc, ida_funcs, ida_bytes, idaapi, traceback
from pathlib import Path

LOG = Path("analysis/s1/p5_bytes_probe.log")
log = []

def hexdump(ea, n=16):
    return ' '.join('%02X' % ida_bytes.get_byte(ea+i) for i in range(n))

def prev_insn(ea, fn_start):
    p = idc.prev_head(ea, fn_start)
    if p == idaapi.BADADDR: return None, None
    return p, idc.print_insn_mnem(p)

try:
    # 1. What's at 0x683C1 (the instruction that ui_loadout_menu_enter is "inside")?
    log.append("=== 0x683C1 area (before ui_loadout_menu_enter at 0x683C5) ===")
    for ea in [0x683BC, 0x683BE, 0x683BF, 0x683C1, 0x683C5, 0x683C6]:
        head = ida_bytes.get_item_head(ea)
        m = idc.print_insn_mnem(ea) if head == ea else ""
        o0 = idc.print_operand(ea, 0) if head == ea else ""
        isz = ida_bytes.get_item_size(ea) if head == ea else 0
        log.append("  0x%X (head=0x%X, isz=%d): %s %s  bytes=%s" % (
            ea, head, isz, m, o0, hexdump(ea, 6)))
    
    # 2. What's at 0x6940B (real start of r30_record_link per status.md)?
    log.append("")
    log.append("=== 0x6940B area (real r30_record_link entry) ===")
    for ea in [0x69407, 0x6940B, 0x6940E]:
        head = ida_bytes.get_item_head(ea)
        m = idc.print_insn_mnem(ea) if head == ea else ""
        o0 = idc.print_operand(ea, 0) if head == ea else ""
        isz = ida_bytes.get_item_size(ea) if head == ea else 0
        f = ida_funcs.get_func(ea)
        log.append("  0x%X fn=%s: %s %s  bytes=%s" % (
            ea, (hex(f.start_ea) if f else "none"), m, o0, hexdump(ea, 6)))
    
    # 3. What's at 0x67F58 (before r30_entry_partial_b at 0x67F59)?
    log.append("")
    log.append("=== 0x67F55..0x67F60 (before cluster start) ===")
    for ea in range(0x67F55, 0x67F70, 1):
        head = ida_bytes.get_item_head(ea)
        if head != ea: continue
        m = idc.print_insn_mnem(ea)
        o0 = idc.print_operand(ea, 0)
        f = ida_funcs.get_func(ea)
        isz = ida_bytes.get_item_size(ea)
        log.append("  0x%X fn=%s isz=%d: %s %s" % (
            ea, (hex(f.start_ea) if f else "none"), isz, m, o0))
    
    # 4. What are the undecoded switch case bodies (0x68A18 etc.)?
    log.append("")
    log.append("=== Undecoded switch case bodies ===")
    for ea in [0x68A18, 0x68A5E, 0x68AE2, 0x68C02, 0x68CC0, 0x68E49, 0x68F20, 0x69123]:
        head = ida_bytes.get_item_head(ea)
        m = idc.print_insn_mnem(ea) if head == ea else ""
        f = ida_funcs.get_func(ea)
        log.append("  0x%X head=%X fn=%s: %r  bytes=%s" % (
            ea, head, (hex(f.start_ea) if f else "none"), m, hexdump(ea, 8)))
    
    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
