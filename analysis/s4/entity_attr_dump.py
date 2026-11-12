"""entity_attr_dump.py — dump farobj_entity_attr_setup and find actual table addresses."""
import idc, ida_bytes, idaapi
from pathlib import Path

_idb = Path(idc.get_idb_path()).parent
LOG = _idb / "entity_attr_dump.log"

log = []

try:
    #  farobj_entity_attr_setup at 0x44352
    fn_ea = 0x44352
    log.append("=== farobj_entity_attr_setup @ 0x%X ===" % fn_ea)
    
    # Dump 50 instructions
    ea = fn_ea
    for i in range(50):
        dis = idc.generate_disasm_line(ea, 0)
        # Get operand values for memory references
        op0 = idc.get_operand_value(ea, 0)
        op1 = idc.get_operand_value(ea, 1)
        log.append("  0x%05X: %-40s  op0=0x%X op1=0x%X" % (ea, dis, op0, op1))
        ea = idc.next_head(ea)
        if ea == idc.BADADDR:
            break
    
    # Now manually extract the table offsets from the mov instructions
    # Look for: mov cx, [bx+NNNN] and mov bx, [bx+NNNN]
    log.append("\n=== Scanning for [bx+offset] patterns ===")
    ea = fn_ea
    for i in range(30):
        mnem = idc.print_insn_mnem(ea)
        if mnem == "mov":
            op_str = idc.print_operand(ea, 1)
            if "bx+" in op_str:
                # Extract offset
                try:
                    off_str = op_str.split("bx+")[1].rstrip("h]")
                    off = int(off_str, 16) if off_str else 0
                    log.append("  0x%05X: %s — offset = 0x%04X (%d)" % (ea, idc.generate_disasm_line(ea, 0), off, off))
                except:
                    pass
        ea = idc.next_head(ea)
        if ea == idc.BADADDR:
            break
    
    # Check what segment DS points to
    log.append("\n=== DS segment info ===")
    # R05_33AE is at IDA address 0x43AEE (seg.start_ea)
    # But DS_BASE for runtime = link_para × 16 + 0x10000
    seg_sel = idc.selector_by_name("R05_33AE")
    seg_33ae_start = idc.get_segm_start(seg_sel) if seg_sel != idc.BADADDR else idc.BADADDR
    if seg_33ae_start != idc.BADADDR:
        log.append("R05_33AE segment start = 0x%X" % seg_33ae_start)
        # Compute the paragraph-aligned base
        # IDA adds 14 bytes (0xE) to align to next paragraph
        # link_para = 0x33AE → DOS base = 0x33AE0 (phys) = 0x43AE0 (IDA flat)
        # But IDA's segment starts at 0x43AEE (14 bytes later)
        log.append("Expected paragraph base = 0x43AE0")
        log.append("Offset of seg_start from para = 0x%X" % (seg_33ae_start - 0x43AE0))
    
    # Read first 20 words from the ACTUAL IDA addresses used in the code
    # From the disassembly, find the mov instructions and use THOSE addresses
    # Let's assume table_b offset is 0x16F4 and table_a is 0x1662 (from the code)
    # DS base in IDA = seg.start_ea
    if seg_33ae_start != idc.BADADDR:
        log.append("\n=== Reading tables using IDA segment base ===")
        table_b_ea = seg_33ae_start + 0x16F4
        table_a_ea = seg_33ae_start + 0x1662
        log.append("Table B @ 0x%X (seg+0x16F4)" % table_b_ea)
        log.append("Table A @ 0x%X (seg+0x1662)" % table_a_ea)
        
        log.append("\nTable B (first 20 entries):")
        for i in range(20):
            w = ida_bytes.get_word(table_b_ea + i * 2)
            lo = w & 0xFF
            log.append("  [%2d] = 0x%04X (class=0x%02X = %3d)" % (i, w, lo, lo))
        
        log.append("\nTable A (first 20 entries):")
        for i in range(20):
            w = ida_bytes.get_word(table_a_ea + i * 2)
            log.append("  [%2d] = 0x%04X" % (i, w))
    
    LOG.write_text("\n".join(log), encoding='utf-8')

except Exception as e:
    LOG.write_text("\n".join(log) + "\n\nERROR:\n" + str(e), encoding='utf-8')

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
