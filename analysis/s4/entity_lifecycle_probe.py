"""entity_lifecycle_probe.py — farobj entity lifecycle functions + class codes."""
import idc, ida_funcs, ida_bytes, idautils, idaapi, ida_segment
import traceback
from pathlib import Path

LOG = Path("analysis/s4/entity_lifecycle.log")

TARGETS = [
    0x213E6,  # farobj_record_lookup_step — the per-farobj step in the depth-sorted loop
    0x3C1BD,  # farobj_slot_update_driver — top-level slot update
    0x2E2D0,  # farobj_sweep_all — sweeps all farobj instances
    0x2E6C2,  # farobj_cmd_interp — command interpreter for farobj
    0x3BB8F,  # farobj_record_ops_exec — the main farobj operations executor
    0x4D8A7,  # farobj_slot_step_spawn — spawning
    0x2EA78,  # entity_slot_pair_create — creates entity slot pair
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
    # Probe the entity class type table
    log.append("=== Entity class code investigation ===")
    # farobj_entity_attr_setup (0x44352) is in R05_33AE
    # It accesses [bx+16F4h] relative to seg R05_33AE
    ENTITY_ATTR = 0x44352
    fn = ida_funcs.get_func(ENTITY_ATTR)
    if fn:
        seg = ida_segment.getseg(ENTITY_ATTR)
        log.append("farobj_entity_attr_setup seg: %s base=0x%X" % (seg_name(ENTITY_ATTR), seg.start_ea if seg else 0))
        # Find the [bx+16F4h] access and [bx+1662h]
        a = ENTITY_ATTR
        while a < fn.end_ea:
            d = idc.generate_disasm_line(a, 0)
            if '16F4' in d or '1662' in d or '14h' in d:
                log.append("  %05X  %s" % (a, d))
            a += ida_bytes.get_item_size(a)
            if a > ENTITY_ATTR + 300: break
    
    # Try to read the type table
    # From the probe: at 443C3: mov bx, [bx+16F4h] with seg R05_33AE
    # The segment starts at some EA. DS is set to 0x1662-relative...
    # Actually check: at 443BD: shl bx,1 then [bx+1662h] and [bx+16F4h]
    # These are DS-relative for overlay R05_33AE
    # Let me find what DS is in that function context
    # Looking at function: it uses [si+N] with DS = overlay, not set internally
    # Segment base R05_33AE
    seg_base = None
    for s_ea in idautils.Segments():
        if '33AE' in seg_name(s_ea):
            seg_base = s_ea
            break
    if seg_base:
        log.append("\nFound R05_33AE segment at 0x%X" % seg_base)
        # Type table B at [bx+0x16F4] relative to this segment = seg_base + 0x16F4 + bx
        # For bx = 0,2,4,6... (index*2)
        table_b_base = seg_base + 0x16F4
        log.append("Type table B at 0x%X:" % table_b_base)
        for i in range(16):
            val = ida_bytes.get_word(table_b_base + i*2)
            log.append("  entry[%2d] bx=%2d  = 0x%04X (%d)" % (i, i*2, val, val))
        
        table_a_base = seg_base + 0x1662
        log.append("Type table A at 0x%X:" % table_a_base)
        for i in range(16):
            val = ida_bytes.get_word(table_a_base + i*2)
            log.append("  entry[%2d] = 0x%04X" % (i, val))
    
    # Main entity lifecycle probes
    for ea in TARGETS:
        fn = ida_funcs.get_func(ea)
        if fn is None or fn.start_ea != ea:
            log.append("\nSKIP 0x%X" % ea)
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

    LOG.write_text("\n".join(log))

except Exception:
    LOG.write_text(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
