#!/usr/bin/env python3
"""Analyze top 10 Level-0 functions from existing level0_disasm.json"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
S4 = ROOT / "analysis" / "s4"

# Load existing disassembly data
level0_data = json.loads((S4 / "level0_disasm.json").read_text())

# Top 10 targets (from callgraph ranking)
TARGETS = [
    "sub_263F6",   # dyn=18079 in=8
    "sub_12890",   # dyn=11513 in=1
    "sub_2295C",   # dyn=11154 in=6
    "sub_22436",   # dyn=9698 in=5
    "sub_2243B",   # dyn=9698 in=5
    "sub_2284B",   # dyn=9189 in=1
    "sub_230D8",   # dyn=8914 in=2
    "sub_22846",   # dyn=8066 in=1
    "sub_23134",   # dyn=7994 in=1
    "sub_22850",   # dyn=7528 in=1
]

def analyze_function(key, data):
    """Analyze a single function from disasm data."""
    info = data.get(key)
    if not info:
        return {"error": "Not found in level0_disasm.json"}
    
    disasm = info.get("disasm", [])
    callers = info.get("callers", [])
    data_refs = info.get("data_refs", [])
    
    # Pattern detection
    patterns = {}
    
    # Check if it's a simple data accessor (mov+ret)
    if len(disasm) <= 10:
        is_simple_accessor = all(
            any(x in line for x in ["mov", "ret", "push", "pop"])
            for line in disasm
        )
        if is_simple_accessor:
            patterns["type"] = "simple_accessor"
    
    # Check for I/O port access
    has_io = any("in " in line or "out " in line for line in disasm)
    if has_io:
        patterns["type"] = "io_accessor"
        patterns["ports"] = [
            line for line in disasm if "in " in line or "out " in line
        ]
    
    # Check for interrupt calls
    has_int = any("int " in line for line in disasm)
    if has_int:
        patterns["type"] = "interrupt_wrapper"
        patterns["interrupts"] = [
            line for line in disasm if "int " in line
        ]
    
    # Check for data table access
    if data_refs:
        patterns["data_access"] = True
        patterns["ref_count"] = len(data_refs)
    
    return {
        "ea": info.get("ea"),
        "name": info.get("name"),
        "size": info.get("size"),
        "seg": info.get("seg"),
        "caller_count": len(callers),
        "callers": [c.get("fn") for c in callers],
        "disasm": disasm,
        "data_refs": data_refs,
        "patterns": patterns,
    }

def main():
    results = {}
    for i, key in enumerate(TARGETS, 1):
        print(f"{i:2d}. Analyzing {key}...")
        results[key] = analyze_function(key, level0_data)
    
    # Save analysis
    out_path = S4 / "level0_batch1_analysis.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_path}")
    
    # Print summary
    print("\n=== ANALYSIS SUMMARY ===")
    for key in TARGETS:
        r = results[key]
        if "error" in r:
            print(f"{key:15s} {r['error']}")
        else:
            ptype = r["patterns"].get("type", "unknown")
            print(f"{key:15s} size={r['size']:3d}B callers={r['caller_count']:2d} pattern={ptype}")

if __name__ == "__main__":
    main()
