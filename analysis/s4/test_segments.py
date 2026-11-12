"""test_segments.py — debug segment enumeration."""
import idc, ida_segment, idautils, idaapi
from pathlib import Path

_idb = Path(idc.get_idb_path()).parent
LOG = _idb / "test_segments.log"

log = []

# Write immediately to confirm script runs
Path(_idb / "test_segments_started.txt").write_text("Started", encoding='utf-8')

try:
    log.append("=== Testing segment enumeration ===\n")
    
    # Test idautils.Segments()
    log.append("Method 1: idautils.Segments()")
    try:
        count = 0
        for seg_ea in idautils.Segments():
            count += 1
            name = idc.get_segm_name(seg_ea)
            seg = ida_segment.getseg(seg_ea)
            sclass = seg.sclass if seg else None
            log.append("  %d: 0x%X = %-15s  sclass=%s (CODE=%s)" % (
                count, seg_ea, name, sclass, idc.SEG_CODE
            ))
            if count >= 10:
                log.append("  ... (stopping at 10)")
                break
        log.append("  Total: %d segments\n" % count)
    except Exception as e:
        log.append("  ERROR: %s\n" % e)
    
    # Test idc.get_first_seg() / idc.get_next_seg()
    log.append("Method 2: idc.get_first_seg() / get_next_seg()")
    try:
        count = 0
        seg_ea = idc.get_first_seg()
        while seg_ea != idc.BADADDR:
            count += 1
            name = idc.get_segm_name(seg_ea)
            log.append("  %d: 0x%X = %s" % (count, seg_ea, name))
            if count >= 10:
                log.append("  ... (stopping at 10)")
                break
            seg_ea = idc.get_next_seg(seg_ea)
        log.append("  Total: %d segments\n" % count)
    except Exception as e:
        log.append("  ERROR: %s\n" % e)
    
    LOG.write_text("\n".join(log), encoding='utf-8')

except Exception as e:
    import traceback
    LOG.write_text("\n".join(log) + "\n\nERROR:\n" + traceback.format_exc(), encoding='utf-8')

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
