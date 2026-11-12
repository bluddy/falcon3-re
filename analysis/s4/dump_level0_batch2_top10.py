#!/usr/bin/env python3
"""Dump bytecode for Level-0 batch 2 top 10 functions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"
CG = ROOT / "analysis" / "traces" / "callgraph_partial.json"

# Batch 2 top 10 (ranks 11-20)
TARGETS = [
    ("sub_100B5", 0x100B5, 6),      # dyn=2953 in=11
    ("sub_22DE6", 0x22DE6, 10),     # dyn=1706 in=3
    ("sub_22F2C", 0x22F2C, 163),    # dyn=1453 in=1
    ("sub_255F6", 0x255F6, 12),     # dyn=1302 in=0
    ("sub_22F15", 0x22F15, 23),     # dyn=603 in=5
    ("sub_22EFE", 0x22EFE, 23),     # dyn=603 in=4
    ("sub_2305B", 0x2305B, 23),     # dyn=534 in=5
    ("sub_1024A", 0x1024A, 30),     # dyn=534 in=2
    ("sub_22440", 0x22440, 5),      # dyn=489 in=2
    ("sub_22445", 0x22445, 16),     # dyn=489 in=2
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
    
    print("=== Level-0 Batch 2 Top 10: Bytecode Dump ===\n")
    
    for key, ea, expected_size in TARGETS:
        fb_entry = fb.get(key, {})
        if not fb_entry or not fb_entry.get("bytes"):
            print(f"{key}  (0x{ea:05X}, {expected_size}B)")
            print("  ERROR: No bytecode in function_bytes.json\n")
            continue
        
        bytecode = fb_entry["bytes"]
        size = len(bytecode) // 2
        
        # Get caller info from callgraph
        callers = [edge[0] for edge in cg["edges"] if edge[1] == key]
        dyn = cg["dyn_target_calls"].get(key, 0)
        static_in = cg["static_in_degree"].get(key, 0)
        
        print(f"{key}  (0x{ea:05X}, {size}B, dyn={dyn}, in={static_in})")
        
        if size <= 10:
            # Tiny/small function - show compact hex
            print(f"  Bytecode: {bytecode}")
        else:
            # Larger function - show formatted with line breaks
            for line in format_bytes(bytecode):
                print(f"  {line}")
        
        if callers:
            caller_list = ', '.join(callers[:5])
            if len(callers) > 5:
                caller_list += f" ... +{len(callers)-5} more"
            print(f"  Callers: {caller_list}")
        else:
            print(f"  Callers: NONE (in_degree=0, indirect calls only)")
        
        print()

if __name__ == "__main__":
    main()
