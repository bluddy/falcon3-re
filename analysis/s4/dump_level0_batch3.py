#!/usr/bin/env python3
"""Dump bytecode for Level-0 batch 3 (ranks 21-35)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"
CG = ROOT / "analysis" / "traces" / "callgraph_partial.json"

# Batch 3 ranks 21-35
TARGETS = [
    ("sub_274D5", 0x274D5, 12),     # dyn=194 in=2
    ("sub_254CA", 0x254CA, 6),      # dyn=90 in=0
    ("sub_254D0", 0x254D0, 12),     # dyn=90 in=0
    ("sub_231A6", 0x231A6, 22),     # dyn=60 in=1
    ("sub_231BC", 0x231BC, 5),      # dyn=47 in=2
    ("sub_231C1", 0x231C1, 5),      # dyn=47 in=2
    ("sub_22DF0", 0x22DF0, 5),      # dyn=46 in=4
    ("sub_22DF5", 0x22DF5, 5),      # dyn=46 in=4
    ("sub_24E46", 0x24E46, 23),     # dyn=34 in=4
    ("sub_27649", 0x27649, 20),     # dyn=33 in=2
    ("sub_2C969", 0x2C969, 8),      # dyn=24 in=2
    ("sub_2765D", 0x2765D, 22),     # dyn=13 in=0
    ("sub_231C6", 0x231C6, 13),     # dyn=9 in=3
    ("sub_23050", 0x23050, 11),     # dyn=9 in=1
    ("sub_10108", 0x10108, 44),     # dyn=8 in=1
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
    fb = json.loads(FB.read_text())
    cg = json.loads(CG.read_text())
    
    print("=== Level-0 Batch 3 (ranks 21-35): Bytecode Dump ===\n")
    
    for key, ea, expected_size in TARGETS:
        fb_entry = fb.get(key, {})
        if not fb_entry or not fb_entry.get("bytes"):
            print(f"{key}  (0x{ea:05X}, {expected_size}B)")
            print("  ERROR: No bytecode in function_bytes.json\n")
            continue
        
        bytecode = fb_entry["bytes"]
        size = len(bytecode) // 2
        
        # Get caller info
        callers = [edge[0] for edge in cg["edges"] if edge[1] == key]
        dyn = cg["dyn_target_calls"].get(key, 0)
        static_in = cg["static_in_degree"].get(key, 0)
        
        print(f"{key}  (0x{ea:05X}, {size}B, dyn={dyn}, in={static_in})")
        
        if size <= 12:
            # Small function - compact hex
            print(f"  Bytecode: {bytecode}")
        else:
            # Larger - formatted
            for line in format_bytes(bytecode):
                print(f"  {line}")
        
        if callers:
            caller_list = ', '.join(callers[:5])
            if len(callers) > 5:
                caller_list += f" ... +{len(callers)-5} more"
            print(f"  Callers: {caller_list}")
        else:
            print(f"  Callers: NONE (indirect only)")
        
        print()

if __name__ == "__main__":
    main()
