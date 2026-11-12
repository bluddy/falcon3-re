"""verify_entity_tables.py — verify entity table names exist in IDA."""
import idc, idaapi
from pathlib import Path

_idb = Path(idc.get_idb_path()).parent
LOG = _idb / "verify_entity_tables.log"

log = []

try:
    # Check entity_attr_table at 0x45150
    name_a = idc.get_name(0x45150)
    log.append("0x45150: %s" % name_a)
    
    # Check entity_class_table at 0x455E2
    name_b = idc.get_name(0x455E2)
    log.append("0x455E2: %s" % name_b)
    
    # Verify they match expected names
    if name_a == "entity_attr_table" and name_b == "entity_class_table":
        log.append("\n✓ SUCCESS: Both entity tables have correct names in IDA")
    else:
        log.append("\n✗ MISMATCH: Expected 'entity_attr_table' and 'entity_class_table'")
    
    LOG.write_text("\n".join(log), encoding='utf-8')

except Exception as e:
    import traceback
    LOG.write_text("\n".join(log) + "\n\nERROR:\n" + traceback.format_exc(), encoding='utf-8')

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
