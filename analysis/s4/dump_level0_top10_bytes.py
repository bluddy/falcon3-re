#!/usr/bin/env python3
"""Dump bytecode for top 10 Level-0 functions (manual disassembly of tiny ones)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
IDA = ROOT / "analysis" / "ida_falconcd"

fb = json.loads((IDA / "function_bytes.json").read_text())
cg = json.loads((ROOT / "analysis" / "traces" / "callgraph_partial.json").read_text())

TARGETS = [
    ("sub_263F6", 0x263F6, 122),
    ("sub_12890", 0x12890, 5),
    ("sub_2295C", 0x2295C, 2),
    ("sub_22436", 0x22436, 5),
    ("sub_2243B", 0x2243B, 5),
    ("sub_2284B", 0x2284B, 5),
    ("sub_230D8", 0x230D8, 92),
    ("sub_22846", 0x22846, 5),
    ("sub_23134", 0x23134, 88),
    ("sub_22850", 0x22850, 5),
]

def format_bytes(hex_str, width=16):
    """Format hex string with spacing."""
    bytelist = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]
    lines = []
    for i in range(0, len(bytelist), width):
        chunk = bytelist[i:i+width]
        lines.append(' '.join(chunk))
    return lines

def main():
    print("=== Top 10 Level-0 Functions: Bytecode Dump ===\n")
    
    for key, ea, expected_size in TARGETS:
        fb_entry = fb.get(key, {})
        if not fb_entry or not fb_entry.get("bytes"):
            print(f"{key}  (0x{ea:05X}, {expected_size}B)")
            print("  ERROR: No bytecode in function_bytes.json\n")
            continue
        
        bytecode = fb_entry["bytes"]
        size = len(bytecode) // 2
        callers = [edge[0] for edge in cg["edges"] if edge[1] == key]
        dyn = cg["dyn_target_calls"].get(key, 0)
        
        print(f"{key}  (0x{ea:05X}, {size}B, dyn={dyn}, {len(callers)} callers)")
        
        if size <= 10:
            # Tiny function - show compact hex
            print(f"  Bytecode: {bytecode}")
        else:
            # Larger function - show formatted
            for line in format_bytes(bytecode):
                print(f"  {line}")
        
        print(f"  Callers: {', '.join(callers[:5])}{' ...' if len(callers) > 5 else ''}")
        print()

if __name__ == "__main__":
    main()
