#!/usr/bin/env python3
"""Analyze the 63 remaining MID targets after P1 splits."""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent.parent
BOUNDARY = ROOT / "analysis" / "traces" / "boundary_report.json"
FB = ROOT / "analysis" / "ida_falconcd" / "function_bytes.json"

def main():
    r = json.loads(BOUNDARY.read_text())
    fb = json.loads(FB.read_text())
    
    mid_targets = r.get("mid", [])
    print(f"=== REMAINING MID TARGETS AFTER P1 SPLITS ===")
    print(f"Total: {len(mid_targets)} (was 96 before P1)\n")
    
    # Group by parent
    by_parent = defaultdict(list)
    for t in mid_targets:
        fn_key = t.get("fn")
        by_parent[fn_key].append(t)
    
    print(f"Unique parent functions: {len(by_parent)}\n")
    
    # Calculate stats
    parent_stats = []
    for fn_key, targets in by_parent.items():
        total_calls = sum(t.get("calls", 0) + t.get("jumps", 0) for t in targets)
        fn_info = fb.get(fn_key, {})
        fn_name = fn_info.get("name", fn_key)
        fn_ea = fn_info.get("ea", 0)
        fn_size = fn_info.get("size", 0)
        
        parent_stats.append({
            "fn": fn_key,
            "fn_name": fn_name,
            "fn_ea": hex(fn_ea),
            "fn_size": fn_size,
            "mid_count": len(targets),
            "total_calls": total_calls,
            "targets": targets,
        })
    
    parent_stats.sort(key=lambda x: -x["total_calls"])
    
    # Top 20
    print("=== TOP 20 REMAINING MID PARENTS BY CALL FREQUENCY ===")
    for i, p in enumerate(parent_stats[:20], 1):
        fn_name = p['fn_name'] if p['fn_name'] else p['fn']
        fn_size = p['fn_size'] if p['fn_size'] is not None else 0
        print(f"{i:2d}. {fn_name:40s} ea={p['fn_ea']} size={fn_size:4d}B")
        print(f"    {p['mid_count']} MID targets, {p['total_calls']:,} total calls")
        for t in p['targets'][:3]:
            offset = t.get('offset', 0)
            offset_val = offset if offset is not None else 0
            print(f"      @ +0x{offset_val:03X}: 0x{t['ida_ea']:05X}  "
                  f"{t.get('calls', 0):,} calls, {t.get('jumps', 0)} jumps")
        if len(p['targets']) > 3:
            print(f"      ... +{len(p['targets'])-3} more")
        print()
    
    # Summary by region
    by_region = defaultdict(int)
    for t in mid_targets:
        region = t.get("region", "unknown")
        by_region[region] += 1
    
    print("\n=== BY REGION ===")
    for region, count in sorted(by_region.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(mid_targets)
        print(f"  {region:20s}: {count:3d} ({pct:5.1f}%)")
    
    # Save analysis
    out = {
        "summary": {
            "total_mid": len(mid_targets),
            "total_calls": sum(t.get("calls", 0) + t.get("jumps", 0) for t in mid_targets),
            "unique_parents": len(by_parent),
            "by_region": dict(by_region),
        },
        "by_parent": parent_stats,
    }
    
    out_path = ROOT / "analysis" / "s4" / "remaining_mid_analysis.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nWrote {out_path}")

if __name__ == "__main__":
    main()
