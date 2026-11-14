"""Diagnostic: simulate what apply_orphan_funcs.py computes for ROOT/MANIFEST."""
import traceback, json
from pathlib import Path
import idaapi

LOG = Path("C:/Users/ybarnoy/projects/falcon3/analysis/s1/check_manifest2.log")
log = []

try:
    # Simulate ROOT as apply_orphan_funcs.py would compute it
    # (the tool's __file__ is tools/apply_orphan_funcs.py)
    tool_path = Path("C:/Users/ybarnoy/projects/falcon3/tools/apply_orphan_funcs.py").resolve()
    ROOT = tool_path.parent.parent
    MANIFEST = ROOT / "registry/orphan_funcs_expected.json"
    log.append("ROOT: %s" % ROOT)
    log.append("MANIFEST: %s" % MANIFEST)
    log.append("exists: %s" % MANIFEST.exists())
    if MANIFEST.exists():
        stat = MANIFEST.stat()
        log.append("size: %d bytes" % stat.st_size)
        raw = MANIFEST.read_bytes()
        log.append("first 10 bytes: %r" % raw[:10])
        text = MANIFEST.read_text(encoding='utf-8')
        log.append("read_text(utf-8) len=%d" % len(text))
        log.append("first 20 chars: %r" % text[:20])
        # Also try read_text() without encoding (default locale)
        text2 = MANIFEST.read_text()
        log.append("read_text() default len=%d" % len(text2))
        log.append("first 20 chars default: %r" % text2[:20])
except Exception:
    log.append(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
LOG.write_text("\n".join(log))
import idc; idc.qexit(0)
