"""
Simplified segment export - run this from IDA's script dialog.
File > Script file... > select this file
"""

import idaapi
import idautils
import idc
import json
import os

# Output file - in same directory as IDB
idb_path = idc.get_idb_path()
output_path = os.path.join(os.path.dirname(idb_path), 'segment_map.json')

print("Starting segment export...")
print(f"Output: {output_path}")

# Wait for analysis
idaapi.auto_wait()

# Get segments
segments = []
for seg_ea in idautils.Segments():
    seg = idaapi.getseg(seg_ea)
    if seg:
        segments.append({
            'name': idaapi.get_segm_name(seg),
            'start_ea': seg.start_ea,
            'end_ea': seg.end_ea,
            'selector': seg.sel,
        })

print(f"Found {len(segments)} segments")

# Get functions with seg:off notation
functions = []
for func_ea in idautils.Functions():
    func = idaapi.get_func(func_ea)
    if func:
        seg = idaapi.getseg(func_ea)
        seg_name = idaapi.get_segm_name(seg) if seg else "?"
        offset = func_ea - seg.start_ea if seg else 0
        
        functions.append({
            'name': idc.get_func_name(func_ea),
            'start_ea': func.start_ea,
            'end_ea': func.end_ea,
            'seg_name': seg_name,
            'offset': offset,
            'segoff': f"{seg_name}:{offset:04X}"
        })

print(f"Found {len(functions)} functions")

# Find multi-entry points (xrefs to mid-function addresses)
print("Finding multi-entry points...")
multi_entry = {}

for func_ea in idautils.Functions():
    func = idaapi.get_func(func_ea)
    if not func:
        continue
    
    func_name = idc.get_func_name(func_ea)
    entries = []
    
    # Check each address in function
    ea = func.start_ea
    while ea < func.end_ea:
        if ea != func.start_ea:  # Skip main entry
            # Count xrefs to this address
            xrefs = list(idautils.CodeRefsTo(ea, 0))
            # Filter out fall-through
            real_xrefs = [x for x in xrefs if x + idc.get_item_size(x) != ea]
            
            if real_xrefs:
                seg = idaapi.getseg(ea)
                seg_name = idaapi.get_segm_name(seg) if seg else "?"
                offset = ea - seg.start_ea if seg else 0
                
                entries.append({
                    'address': ea,
                    'segoff': f"{seg_name}:{offset:04X}",
                    'offset_from_start': ea - func.start_ea,
                    'xref_count': len(real_xrefs)
                })
        
        ea = idc.next_head(ea, func.end_ea)
    
    if entries:
        multi_entry[func_name] = entries

print(f"Found {len(multi_entry)} multi-entry functions")

# Write output
data = {
    'segments': segments,
    'functions': functions,
    'multi_entry_functions': multi_entry,
    'summary': {
        'total_segments': len(segments),
        'total_functions': len(functions),
        'multi_entry_count': len(multi_entry)
    }
}

with open(output_path, 'w') as f:
    json.dump(data, f, indent=2)

print(f"✓ Export complete: {output_path}")
print(f"  Segments: {len(segments)}")
print(f"  Functions: {len(functions)}")
print(f"  Multi-entry: {len(multi_entry)}")
