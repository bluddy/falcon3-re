"""level2_probe.py — targeted probe for key Level-2 functions and op_dispatch table."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment, ida_name
import traceback
from pathlib import Path

LOG  = Path("analysis/s4/level2_disasm.log")

TARGETS = [
    # Level-2 high-value
    0x251C3,  # flag_table_pop_far_thunk  543K dyn
    0x25087,  # flag_block_build_far_thunk  161K dyn  
    0x14EAE,  # farobj_tile_copy_resolve  397K dyn (key!)
    0x28874,  # pos_diff_norm  18K dyn
    0x1796C,  # channel_release  8.8K dyn (audio)
    0x17835,  # channel_volume_store  7.9K dyn (audio)
    0x1D796,  # sbi_level_write_6  2.3K dyn (audio/OPL)
    0x12534,  # entity_step_flags  216B, 28 callers
    0x142DA,  # tile_world_index_3334  19K dyn
    0x1656F,  # tile_index_clamp_5f  10K dyn
    0x2245A,  # draw_from_struct  649 dyn
    # op_dispatch table probe: look up what BX=0,2,6,8,0xA,0xE dispatch to
    0x2257B,  # op_dispatch itself — get the table
]

log = []

def seg_name(ea):
    s = ida_segment.getseg(ea)
    return ida_segment.get_segm_name(s) if s else "?"

def callers_of(ea, limit=5):
    result = []
    for xr in idautils.XrefsTo(ea, 0):
        if not xr.iscode: continue
        fn = ida_funcs.get_func(xr.frm)
        nm = idc.get_func_name(fn.start_ea) if fn else "?"
        result.append(nm)
        if len(result) >= limit: break
    return result

try:
    for ea in TARGETS:
        fn = ida_funcs.get_func(ea)
        if fn is None or fn.start_ea != ea:
            log.append("SKIP 0x%X: not a fn start" % ea)
            continue
        name = idc.get_func_name(ea)
        size = fn.end_ea - fn.start_ea
        log.append("\n=== 0x%X  %s  %dB  %s ===" % (ea, name, size, seg_name(ea)))
        a, limit = fn.start_ea, 60
        while a < fn.end_ea and limit > 0:
            log.append("  %05X  %s" % (a, idc.generate_disasm_line(a, 0)))
            a += ida_bytes.get_item_size(a)
            limit -= 1
        if a < fn.end_ea:
            log.append("  ... (%dB more)" % (fn.end_ea - a))
        log.append("  Callers: %s" % callers_of(ea))

    # op_dispatch table: read the near-pointer table at cs:op_dispatch_table
    # The table is indexed as [bx] where bx = op_code
    # Find it by looking at what op_dispatch calls
    log.append("\n=== op_dispatch table contents ===")
    OP_DISPATCH_EA = 0x2257B
    # Scan the function for the table address
    fn = ida_funcs.get_func(OP_DISPATCH_EA)
    if fn:
        a = fn.start_ea
        while a < fn.end_ea:
            d = idc.generate_disasm_line(a, 0)
            if "op_dispatch_table" in d or "off_22060" in d or ("call" in d and "cs:" in d):
                log.append("  %05X  %s" % (a, d))
                # Try to get the table address from the instruction
                for xr in idautils.DataRefsFrom(a):
                    log.append("    -> table at 0x%X" % xr)
                    # Read 20 entries (near pointers = 2 bytes each)
                    for i in range(20):
                        entry_ea = xr + i*2
                        target = ida_bytes.get_word(entry_ea)
                        if target == 0 or target > 0xFFFF: continue
                        # target is a near offset; get its name
                        fn2 = ida_funcs.get_func(target)
                        tname = idc.get_func_name(fn2.start_ea) if fn2 and fn2.start_ea == target else ("sub_%X" % target)
                        # Also get disasm of first 2 instructions
                        d1 = idc.generate_disasm_line(target, 0) if fn2 else "?"
                        log.append("      [%2d] 0x%04X -> %s   %s" % (i, target, tname, d1))
                break
            a += ida_bytes.get_item_size(a)

    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
