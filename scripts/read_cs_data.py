"""
Read data from CS segment at specific offsets.
"""

import idc
import idaapi
import json
from pathlib import Path

print("=" * 70)
print("READING CS SEGMENT DATA")
print("=" * 70)
print()

idaapi.auto_wait()

# CS segment offsets
offsets = {
    "scale_x": 0x35BD,
    "div_x": 0x35C3,
    "scale_y": 0x35BF,
    "div_y": 0x35C5,
    "scale_z": 0x35C1,
    "div_z": 0x35C7,
}

print("Finding CS segment...")

# Find the code segment containing fixed_vec3_accumulate_a
func_addr = 0x22C91
seg = idaapi.getseg(func_addr)

if seg:
    print(f"Found segment: {idc.get_segm_name(seg.start_ea)}")
    print(f"  Start: 0x{seg.start_ea:X}")
    print(f"  End: 0x{seg.end_ea:X}")
    print()
    
    # Calculate absolute addresses
    print("Calculating absolute addresses:")
    results = {}
    for name, offset in offsets.items():
        abs_addr = seg.start_ea + offset
        print(f"  {name:10s}: CS:0x{offset:04X} -> 0x{abs_addr:X}")
        
        # Try to read the word
        value = idc.get_wide_word(abs_addr)
        signed_value = value if value < 32768 else value - 65536
        print(f"               Value: {value} (0x{value:04X}) signed: {signed_value}")
        
        results[name] = value
    
    print()
    
    # Save results
    output_path = Path(__file__).parent.parent / "temp" / "cs_data.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Saved to: {output_path}")
else:
    print("ERROR: Could not find segment!")

print()
print("=" * 70)

idc.qexit(0)
