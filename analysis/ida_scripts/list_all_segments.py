#!/usr/bin/env python3
"""
List all segments in the database to find 6E1E.
"""

import idc
import idaapi
import idautils
import json

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("LIST ALL SEGMENTS")
    print("="*80)
    print()
    
    segments = []
    
    for seg_ea in idautils.Segments():
        seg_name = idc.get_segm_name(seg_ea)
        seg_end = idc.get_segm_end(seg_ea)
        seg_size = seg_end - seg_ea
        
        segments.append({
            'name': seg_name,
            'start': hex(seg_ea),
            'end': hex(seg_end),
            'size': seg_size
        })
        
        print(f"{seg_name:<30} {seg_ea:#010x} - {seg_end:#010x}  ({seg_size:8d} bytes)")
    
    print()
    print(f"[+] Total segments: {len(segments)}")
    
    # Save
    output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\all_segments.json'
    with open(output_path, 'w') as f:
        json.dump({'segments': segments, 'count': len(segments)}, f, indent=2)
    
    print(f"[+] Saved to {output_path}")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
