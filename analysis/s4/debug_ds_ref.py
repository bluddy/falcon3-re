"""debug_ds_ref.py — manually decode the DS references at 0x443BF and 0x443C3."""
import idc, ida_bytes, ida_segment, idautils, idaapi
from pathlib import Path

_idb = Path(idc.get_idb_path()).parent
LOG = _idb / "debug_ds.log"

log = []

try:
    # The two instructions:
    # 0x443BF: mov cx, [bx+1662h]
    # 0x443C3: mov bx, [bx+16F4h]
    
    ea1 = 0x443BF
    ea2 = 0x443C3
    
    log.append("=== Instruction analysis ===")
    log.append("0x%X: %s" % (ea1, idc.generate_disasm_line(ea1, 0)))
    log.append("  operand 1: %s" % idc.print_operand(ea1, 1))
    log.append("  get_operand_value(1) = 0x%X" % idc.get_operand_value(ea1, 1))
    
    log.append("")
    log.append("0x%X: %s" % (ea2, idc.generate_disasm_line(ea2, 0)))
    log.append("  operand 1: %s" % idc.print_operand(ea2, 1))
    log.append("  get_operand_value(1) = 0x%X" % idc.get_operand_value(ea2, 1))
    
    # Now find what segment DS points to in this function
    fn = ida_funcs.get_func(ea1)
    log.append("\n=== Function context ===")
    log.append("Function: %s @ 0x%X" % (idc.get_func_name(fn.start_ea), fn.start_ea))
    
    # Check all segments
    log.append("\n=== All segments ===")
    for seg_ea in idautils.Segments():
        seg = ida_segment.getseg(seg_ea)
        name = idc.get_segm_name(seg_ea)
        log.append("  %s: 0x%X - 0x%X (size=0x%X)" % (name, seg.start_ea, seg.end_ea, seg.end_ea - seg.start_ea))
        if "R05" in name:
            log.append("    ^^^ This is likely the DS segment ^^^")
            # Read 10 words starting from offset 0x1662
            log.append("    First 10 words at +0x1662:")
            for i in range(10):
                w = ida_bytes.get_word(seg.start_ea + 0x1662 + i * 2)
                log.append("      [%d] = 0x%04X" % (i, w))
            log.append("    First 10 words at +0x16F4:")
            for i in range(10):
                w = ida_bytes.get_word(seg.start_ea + 0x16F4 + i * 2)
                log.append("      [%d] = 0x%04X (lo=0x%02X)" % (i, w, w & 0xFF))
    
    LOG.write_text("\n".join(log), encoding='utf-8')

except Exception as e:
    import traceback
    LOG.write_text("\n".join(log) + "\n\nERROR:\n" + traceback.format_exc(), encoding='utf-8')

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
