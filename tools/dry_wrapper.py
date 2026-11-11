"""Wrapper to run apply_orphan_funcs.py in DRY mode."""
import os
os.environ["OFDRY"] = "1"
exec(open("tools/apply_orphan_funcs.py").read())
