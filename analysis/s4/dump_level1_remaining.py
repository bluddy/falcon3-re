#!/usr/bin/env python3
"""
Dump bytecode for remaining Level-1 non-wrapper functions that need decode.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"

# Load function bytes
fb = json.loads(FB.read_text())

# Functions to dump (from Level-1 analysis - non-wrappers needing decode)
targets = [
    'sub_11A7D',  # 106B, 5 calls, complex initialization
    'sub_10DA7',  # 31B, 4 calls, interrupt-based operation
]

for fn in targets:
    if fn in fb:
        bytecode = fb[fn]
        print(f"\n## {fn} ({len(bytecode)//2}B)")
        print(f"```\nBytecode: {bytecode}\n```")
    else:
        print(f"\n## {fn} - NOT FOUND in function_bytes.json")
