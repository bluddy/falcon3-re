"""rendering_probe.py — view_projection callers + entity class investigation."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment, ida_bytes as idb
import traceback
from pathlib import Path

LOG = Path("analysis/s4/rendering_disasm.log")

TARGETS = [
    0x20D84,  # farobj_tile_align_project (caller of view_projection)
    0x20E9A,  # coord_point_group_project (caller)
    0x213E5,  # farobj_batch_build_project (caller, the full batch renderer)
    0x1D37C,  # viewlist_project_flagged (called by game_frame_pipeline_step)
    0x1740D,  # sound_device_init
    0x20BDB,  # view_projection itself — read the entity class constants
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
    # First: probe entity class codes from farobj_type_gate_test area
    # and the entity_slot_create to find where class codes are set
    log.append("=== Looking for entity class code assignments ===")
    
    # Search for the values 0x12, 0x14, 0x33, 0x38 near farobj_entity_attr_setup
    # and entity_slot_create
    ENTITY_ATTR_SETUP = 0x44352
    fn = ida_funcs.get_func(ENTITY_ATTR_SETUP)
    if fn:
        # Look for the type table lookup that sets [SI+14h]
        # At 443C7: mov [si+14h], bx where bx = [bx+16F4h]
        # Find that table at 0x16F4 relative to some base
        # From entity_attr_setup: shl bx, 1; mov cx, [bx+1662h]; mov bx, [bx+16F4h]
        # AX in BX after lookup is the entity_class word
        # Let's try to read the table at DS:0x16F4 / 0x1662
        # Actually this is relative to seg005 (overlay R05_xxx)
        log.append("entity_attr_setup at 0x%X in seg %s" % (ENTITY_ATTR_SETUP, seg_name(ENTITY_ATTR_SETUP)))
        a = ENTITY_ATTR_SETUP
        # Read the type assignment block
        for _ in range(60):
            d = idc.generate_disasm_line(a, 0)
            if '14h' in d or '1662' in d or '16F4' in d or 'type' in d.lower():
                log.append("  %05X  %s" % (a, d))
            a += ida_bytes.get_item_size(a)
            if a > ENTITY_ATTR_SETUP + 100: break

    # Probe the main target functions
    for ea in TARGETS:
        fn = ida_funcs.get_func(ea)
        if fn is None or fn.start_ea != ea:
            log.append("\nSKIP 0x%X (not fn start)" % ea)
            continue
        name = idc.get_func_name(ea)
        size = fn.end_ea - fn.start_ea
        log.append("\n=== 0x%X  %s  %dB  %s ===" % (ea, name, size, seg_name(ea)))
        a, lim = fn.start_ea, 55
        while a < fn.end_ea and lim > 0:
            log.append("  %05X  %s" % (a, idc.generate_disasm_line(a, 0)))
            a += ida_bytes.get_item_size(a)
            lim -= 1
        if a < fn.end_ea:
            log.append("  ... (%dB more)" % (fn.end_ea - a))
        log.append("  Callers: %s" % callers_of(ea))

    # Also find viewlist_project_flagged
    for fn_ea in idautils.Functions():
        nm = idc.get_func_name(fn_ea)
        if 'viewlist' in nm and 'project' in nm:
            fn = ida_funcs.get_func(fn_ea)
            size = fn.end_ea - fn_ea
            log.append("\n=== 0x%X  %s  %dB  %s ===" % (fn_ea, nm, size, seg_name(fn_ea)))
            a, lim = fn_ea, 40
            while a < fn.end_ea and lim > 0:
                log.append("  %05X  %s" % (a, idc.generate_disasm_line(a, 0)))
                a += ida_bytes.get_item_size(a)
                lim -= 1
            if a < fn.end_ea:
                log.append("  ... (%dB more)" % (fn.end_ea - a))
            log.append("  Callers: %s" % callers_of(fn_ea))

    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
