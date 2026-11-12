"""Diagnostic: check MANIFEST path and content in IDA's Python environment."""
import traceback, json
from pathlib import Path
import idaapi

LOG = Path("C:/Users/ybarnoy/projects/falcon3/analysis/s1/check_manifest.log")
log = []

try:
    ROOT = Path(__file__).resolve().parent.parent
    MANIFEST = ROOT / "registry/orphan_funcs_expected.json"
    log.append("__file__: %s" % __file__)
    log.append("ROOT: %s" % ROOT)
    log.append("MANIFEST: %s" % MANIFEST)
    log.append("exists: %s" % MANIFEST.exists())
    if MANIFEST.exists():
        stat = MANIFEST.stat()
        log.append("size: %d bytes" % stat.st_size)
        # Try reading with explicit encoding
        try:
            text = MANIFEST.read_text(encoding='utf-8')
            log.append("read_text(utf-8) len=%d" % len(text))
            log.append("first 50 chars: %r" % text[:50])
        except Exception as e:
            log.append("read_text(utf-8) FAILED: %s" % e)
        # Try reading as bytes
        try:
            raw = MANIFEST.read_bytes()
            log.append("read_bytes() len=%d" % len(raw))
            log.append("first 10 bytes: %r" % raw[:10])
        except Exception as e:
            log.append("read_bytes() FAILED: %s" % e)
except Exception:
    log.append(traceback.format_exc())

idaapi.set_database_flag(idaapi.DBFL_KILL)
LOG.write_text("\n".join(log))
import idc; idc.qexit(0)
