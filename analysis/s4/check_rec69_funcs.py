#!/usr/bin/env python3
import json

fb = json.load(open('../ida_falconcd/function_bytes.json'))

# Record 69 IDA range: 0x706E0..0x8BA97 (base + 84359 bytes)
r69_start = 0x706E0
r69_end = 0x706E0 + 84359

r69_funcs = [(f, d) for f, d in fb.items() if r69_start <= d['ea'] < r69_end]
r69_funcs.sort(key=lambda x: x[1]['ea'])

print(f"Record 69 IDA range: 0x{r69_start:05X}..0x{r69_end:05X}")
print(f"Functions in this range: {len(r69_funcs)}\n")

if r69_funcs:
    print(f"First 10 functions:")
    for f, d in r69_funcs[:10]:
        print(f"  {f}: 0x{d['ea']:05X} ({d['size']}B)")
    
    print(f"\n... {len(r69_funcs) - 10} more ..." if len(r69_funcs) > 10 else "")
    
    # Check if computed addresses are near any functions
    computed_addrs = [0x7E06C, 0x80AEC, 0x821EC, 0x838AC, 0x846FC, 0x858BC, 0x8619C]
    print(f"\n\nChecking computed addresses against actual functions:")
    for addr in computed_addrs:
        nearest = min(r69_funcs, key=lambda x: abs(x[1]['ea'] - addr))
        dist = addr - nearest[1]['ea']
        print(f"  0x{addr:05X}: nearest is {nearest[0]} at 0x{nearest[1]['ea']:05X} (off by {dist:+d} bytes)")
else:
    print("NO FUNCTIONS FOUND in record 69 range!")
    print("\nThis means either:")
    print("  1. Record 69 is not placed/analyzed in the IDB")
    print("  2. It contains only data, not code")
    print("  3. The IDA address calculation is wrong")
