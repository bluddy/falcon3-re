#!/usr/bin/env python3
"""Extract top 10 Level-0 function info from existing IDA exports."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
IDA = ROOT / "analysis" / "ida_falconcd"

# Load existing data
cls = json.loads((IDA / "classification.json").read_text())
fb = json.loads((IDA / "function_bytes.json").read_text())
cg = json.loads((ROOT / "analysis" / "traces" / "callgraph_partial.json").read_text())

# Top 10 by (dyn DESC, in DESC)
TARGETS = [
    "sub_263F6",   # 0x263F6  dyn=18079 in=8  122B
    "sub_12890",   # 0x12890  dyn=11513 in=1    5B
    "sub_2295C",   # 0x2295C  dyn=11154 in=6    2B
    "sub_22436",   # 0x22436  dyn=9698 in=5     5B
    "sub_2243B",   # 0x2243B  dyn=9698 in=5     5B
    "sub_2284B",   # 0x2284B  dyn=9189 in=1     5B
    "sub_230D8",   # 0x230D8  dyn=8914 in=2    92B
    "sub_22846",   # 0x22846  dyn=8066 in=1     5B
    "sub_23134",   # 0x23134  dyn=7994 in=1    88B
    "sub_22850",   # 0x22850  dyn=7528 in=1     5B
]

def main():
    print("=== Extracting top 10 Level-0 functions ===")
    result = {}
    
    for key in TARGETS:
        info = cls.get(key)
        if not info:
            print(f"  {key}: NOT FOUND in classification.json")
            result[key] = {"error": "Not found"}
            continue
        
        ea = info["ea"]
        size = info["size"]
        seg = info.get("segment", "?")
        
        # Get function bytes if available
        fb_entry = fb.get(key, {})
        bytecode = fb_entry.get("bytes", "")
        
        # Get callgraph info
        dyn = cg["dyn_target_calls"].get(key, 0)
        static_in = cg["static_in_degree"].get(key, 0)
        
        # Find callers from edges
        callers = []
        for edge in cg["edges"]:
            if edge[1] == key:  # edge = [caller, callee]
                callers.append(edge[0])
        
        # Find callees (should be 0 for Level-0)
        callees = []
        for edge in cg["edges"]:
            if edge[0] == key:
                callees.append(edge[1])
        
        result[key] = {
            "ea": hex(ea),
            "size": size,
            "seg": seg,
            "class": info.get("class", "?"),
            "dyn_calls": dyn,
            "static_in_degree": static_in,
            "callers": callers,
            "callees": callees,
            "has_bytes": len(bytecode) > 0,
            "bytes_len": len(bytecode) // 2 if bytecode else 0,
        }
        
        print(f"  {key:13s} ea=0x{ea:05X} size={size:3d}B dyn={dyn:5d} in={static_in:2d} callers={len(callers):2d}")
    
    out_path = ROOT / "analysis" / "s4" / "level0_top10_info.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nWrote {out_path}")
    
    # Summary
    print("\n=== PATTERNS ===")
    tiny_fns = [k for k in TARGETS if result.get(k, {}).get("size", 999) <= 10]
    print(f"Tiny functions (<=10B): {len(tiny_fns)}")
    for k in tiny_fns:
        r = result[k]
        print(f"  {k:13s} {r['size']:2d}B  dyn={r['dyn_calls']:5d}  callers={len(r['callers'])}")

if __name__ == "__main__":
    main()
