import json
import struct
from pathlib import Path

# 1. Inspect ISR.json
with open('analysis/isldat_coast_edges/ISR.json') as f:
    isr_data = json.load(f)

print(f"Total records in ISR.json: {len(isr_data['records'])}")
for r in isr_data['records']:
    off = r['off']
    attr = r['attr']
    x_nm = r['x_nm']
    y_nm = r['y_nm']
    box = r['box']
    lines = r['polylines']
    print(f"0x{off:04X} a=0x{attr:02X} (x={x_nm:6.2f}, y={y_nm:6.2f}) box={box} rings={r['rings']} seams={r['seam_edges']} lines={len(lines)}")
    for ln in lines:
        pts = ln['pts']
        print(f"     line: closed={ln['closed']} pts={pts}")
