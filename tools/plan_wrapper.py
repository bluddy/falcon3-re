"""Wrapper to run apply_orphan_funcs.py in PLAN mode."""
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
os.environ["OFMODE"] = "plan"
# verify it's set
assert os.environ.get("OFMODE") == "plan", "OFMODE not set!"
script = (ROOT / "tools" / "apply_orphan_funcs.py").read_text(encoding="utf-8")
exec(compile(script, str(ROOT / "tools" / "apply_orphan_funcs.py"), "exec"))
