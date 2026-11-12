"""test_probe.py — minimal IDA script to verify execution."""
import idc, idaapi
from pathlib import Path

try:
    _idb = Path(idc.get_idb_path()).parent
    log_path = _idb / "test_probe.log"
    log_path.write_text("IDA probe executed successfully\n", encoding='utf-8')
except Exception as e:
    Path("test_probe_error.txt").write_text(str(e))

idaapi.set_database_flag(idaapi.DBFL_KILL)
idc.qexit(0)
