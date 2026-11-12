#!/usr/bin/env python3
"""
Dump bytecode for Level-2 non-wrapper functions that need decode.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"

# Load function bytes
fb = json.loads(FB.read_text())

# Functions to dump (from Level-2 analysis - non-wrappers with dyn>0)
targets = [
    'sub_256A3',  # 10222 calls (highest Level-2 non-wrapper)
    'sub_2501A',  # 488 calls
    'sub_276B4',  # 194 calls
    'sub_100C1',  # 8 calls
]

for fn in targets:
    if fn in fb:
        data = fb[fn]
        if isinstance(data, dict):
            bytecode = data.get('bytes', '')
            size = data.get('size', len(bytecode)//2)
        else:
            bytecode = data
            size = len(bytecode)//2
        print(f"\n## {fn} ({size}B)")
        print(f"```\nBytecode: {bytecode}\n```")
    else:
        print(f"\n## {fn} - NOT FOUND in function_bytes.json")
