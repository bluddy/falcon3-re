"""read_entity_tables.py — read entity type tables using correct DS base.

The mov instructions at 0x443BF and 0x443C3 use DS:0x1662 and DS:0x16F4.
The DS register points to R05_33AE segment, which IDA places at 0x43AEE.
So the actual table addresses are:
  - Table A (attr) = 0x43AEE + 0x1662 = 0x45550
  - Table B (class) = 0x43AEE + 0x16F4 = 0x455E2
"""
import idc, ida_bytes, idaapi
from pathlib import Path

_idb = Path(idc.get_idb_path()).parent
LOG = _idb / "entity_tables.log"
OUT = _idb / "entity_tables.json"

log = []
results = {}

try:
    # R05_33AE segment starts at 0x43AEE in IDA
    DS_BASE = 0x43AEE
    
    table_a_ea = DS_BASE + 0x1662   # 0x45550
    table_b_ea = DS_BASE + 0x16F4   # 0x455E2
    
    log.append("DS_BASE (R05_33AE IDA start) = 0x%X" % DS_BASE)
    log.append("Table A (attr) @ 0x%X (DS+0x1662)" % table_a_ea)
    log.append("Table B (class) @ 0x%X (DS+0x16F4)" % table_b_ea)
    log.append("")
    
    # Read 40 entries from each
    table_a = []
    table_b = []
    
    log.append("=== Table A (entity attributes) ===")
    for i in range(40):
        w = ida_bytes.get_word(table_a_ea + i * 2)
        table_a.append({"i": i, "word": "0x%04X" % w})
        log.append("  A[%2d] = 0x%04X (%5d)" % (i, w, w))
    
    log.append("")
    log.append("=== Table B (entity class codes) ===")
    for i in range(40):
        w = ida_bytes.get_word(table_b_ea + i * 2)
        lo = w & 0xFF
        table_b.append({"i": i, "word": "0x%04X" % w, "class": "0x%02X" % lo})
        log.append("  B[%2d] = 0x%04X → class = 0x%02X (%3d)" % (i, w, lo, lo))
    
    results["ds_base"] = "0x%X" % DS_BASE
    results["table_a_ea"] = "0x%X" % table_a_ea
    results["table_b_ea"] = "0x%X" % table_b_ea
    results["table_a"] = table_a
    results["table_b"] = table_b
    
    import json
    OUT.write_text(json.dumps(results, indent=1), encoding='utf-8')
    LOG.write_text("\n".join(log), encoding='utf-8')
    log.append("\nSuccess: wrote %s" % OUT)

except Exception as e:
    import traceback
    LOG.write_text("\n".join(log) + "\n\nERROR:\n" + traceback.format_exc(), encoding='utf-8')

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
