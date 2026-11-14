"""Debug plan mode failure."""
import os, idaapi, traceback
from pathlib import Path
LOG = Path("analysis/s1/plan_debug.log")
log = []
try:
    os.environ["OFMODE"] = "plan"
    log.append("OFMODE set to: %r" % os.environ.get("OFMODE"))
    exec(Path("tools/apply_orphan_funcs.py").read_text(encoding="utf-8"),
         {"__file__": "tools/apply_orphan_funcs.py"})
    log.append("script finished OK")
except SystemExit as e:
    log.append("SystemExit: %r" % e)
except Exception:
    log.append("EXCEPTION:\n" + traceback.format_exc())
LOG.write_text("\n".join(log))
idaapi.set_database_flag(idaapi.DBFL_KILL)
idaapi.qexit(0)
