#!/usr/bin/env python3
"""Analyze MID-body boundary errors from boundary_report.json."""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
BOUNDARY = ROOT / "analysis" / "traces" / "boundary_report.json"
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"

def main():
    r = json.loads(BOUNDARY.read_text())
    fb = json.loads(FB.read_text())
    
    # Extract MID targets
    mid_targets = [t for t in r.get("mid", [])]
    print(f"=== MID-BODY BOUNDARY ERRORS ===")
    print(f"Total MID targets: {len(mid_targets)}")
    print(f"Total calls+jumps: {sum(t['calls'] + t['jumps'] for t in mid_targets)}\n")
    
    # Group by parent function
    by_parent = defaultdict(list)
    for t in mid_targets:
        fn_key = t.get("fn")
        by_parent[fn_key].append(t)
    
    print(f"Unique parent functions with MID targets: {len(by_parent)}\n")
    
    # Rank by total call frequency
    parent_stats = []
    for fn_key, targets in by_parent.items():
        total_calls = sum(t['calls'] + t['jumps'] for t in targets)
        fn_info = fb.get(fn_key, {})
        fn_size = fn_info.get("size", 0)
        fn_name = fn_info.get("name", None)
        fn_ea = fn_info.get("ea", 0)
        
        parent_stats.append({
            "fn": fn_key,
            "fn_name": fn_name if fn_name else fn_key,
            "fn_ea": hex(fn_ea),
            "fn_size": fn_size,
            "mid_count": len(targets),
            "total_calls": total_calls,
            "targets": targets,
        })
    
    parent_stats.sort(key=lambda x: -x["total_calls"])
    
    # Top 20 by call frequency
    print("=== TOP 20 PARENT FUNCTIONS BY CALL FREQUENCY ===")
    for i, p in enumerate(parent_stats[:20], 1):
        print(f"{i:2d}. {p['fn_name']:40s} ea={p['fn_ea']} size={p['fn_size']:4d}B")
        print(f"    {p['mid_count']} MID targets, {p['total_calls']:,} total calls")
        for t in p['targets'][:3]:  # Show first 3 targets
            print(f"      @ +0x{t['offset']:03X}: {t['calls']:,} calls, {t['jumps']} jumps")
        if len(p['targets']) > 3:
            print(f"      ... +{len(p['targets'])-3} more")
        print()
    
    # Save full report
    out_path = ROOT / "analysis" / "s4" / "mid_boundary_analysis.json"
    with open(out_path, "w") as f:
        json.dump({
            "summary": {
                "total_mid_targets": len(mid_targets),
                "total_calls": sum(t['calls'] + t['jumps'] for t in mid_targets),
                "unique_parent_fns": len(by_parent),
            },
            "by_parent": parent_stats,
        }, f, indent=2)
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
