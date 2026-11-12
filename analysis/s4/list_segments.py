"""
List all segments to find DGROUP.
"""

import idc
import idaapi
import idautils
import json

print("="*80)
print("LISTING ALL SEGMENTS")
print("="*80)

idaapi.auto_wait()

segments = []

for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    if seg:
        seg_name = idaapi.get_segm_name(seg)
        seg_info = {
            "name": seg_name,
            "start": hex(seg.start_ea),
            "end": hex(seg.end_ea),
            "size": seg.end_ea - seg.start_ea,
            "selector": hex(seg.sel)
        }
        segments.append(seg_info)
        
        if "group" in seg_name.lower() or "data" in seg_name.lower():
            print(f"⭐ {seg_name}: {hex(seg.start_ea)} - {hex(seg.end_ea)} (selector {hex(seg.sel)})")
        else:
            print(f"   {seg_name}: {hex(seg.start_ea)} - {hex(seg.end_ea)}")

print(f"\nTotal segments: {len(segments)}")

# Save
output_file = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\segments_list.json"
with open(output_file, "w") as f:
    json.dump({"segments": segments, "count": len(segments)}, f, indent=2)

print(f"Saved to: {output_file}")
idc.qexit(0)
