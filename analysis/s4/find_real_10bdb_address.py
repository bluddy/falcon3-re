#!/usr/bin/env python3
"""
Find the real IDA segment:offset for 0x10BDB based on observed segments.
"""

print("="*80)
print("FINDING REAL IDA ADDRESS FOR sub_10BDB")
print("="*80)

# Observed facts:
# 1. sub_256A3 (linear 0x256A3) is at seg020:5FED
# 2. sub_10B1C (linear 0x10B1C) is at seg002:02DC

# From these, we can calculate the segment bases

# For sub_256A3:
linear_256a3 = 0x256A3
seg020_offset = 0x5FED

# Linear address = seg_base + offset
# So: seg020_base = linear - offset
seg020_base = linear_256a3 - seg020_offset
print(f"\nsub_256A3:")
print(f"  Linear: 0x{linear_256a3:05X}")
print(f"  IDA: seg020:0x{seg020_offset:04X}")
print(f"  => seg020 base: 0x{seg020_base:05X}")

# For sub_10B1C:
linear_10b1c = 0x10B1C
seg002_offset = 0x02DC

seg002_base = linear_10b1c - seg002_offset
print(f"\nsub_10B1C:")
print(f"  Linear: 0x{linear_10b1c:05X}")
print(f"  IDA: seg002:0x{seg002_offset:04X}")
print(f"  => seg002 base: 0x{seg002_base:05X}")

# Now calculate where 0x10BDB should be
target_linear = 0x10BDB

print(f"\n" + "="*80)
print(f"TARGET: 0x{target_linear:05X}")
print("="*80)

# Check which segment it belongs to
if target_linear >= seg020_base:
    offset_in_seg020 = target_linear - seg020_base
    print(f"\nIf in seg020:")
    print(f"  Address: seg020:0x{offset_in_seg020:04X}")
elif target_linear >= seg002_base:
    offset_in_seg002 = target_linear - seg002_base
    print(f"\nIf in seg002:")
    print(f"  Address: seg002:0x{offset_in_seg002:04X}")
else:
    print(f"\nTarget is in an earlier segment (before seg002)")

# The target 0x10BDB is between 0x10B1C (seg002:02DC) and the next function
# So it should be in seg002, just after offset 02DC

gap_start = 0x10B46  # Where sub_10B1C ends (from Finding 207)
target = 0x10BDB
gap_in_seg002_start = gap_start - seg002_base
target_in_seg002 = target - seg002_base

print(f"\n" + "="*80)
print("CALCULATED ADDRESSES")
print("="*80)

print(f"\nsub_10B1C ends at:")
print(f"  Linear: 0x{gap_start:05X}")
print(f"  IDA: seg002:0x{gap_in_seg002_start:04X}")

print(f"\nsub_10BDB should be at:")
print(f"  Linear: 0x{target:05X}")
print(f"  IDA: seg002:0x{target_in_seg002:04X}")

print(f"\nGap size: {target - gap_start} bytes (0x{target - gap_start:X})")

print(f"\n" + "="*80)
print("HOW TO NAVIGATE IN IDA")
print("="*80)

print(f"""
Based on your IDA's segment layout:

1. Go to sub_10B1C:
   Press 'G', type: seg002:{seg002_offset:04X}
   (or just find sub_10B1C in Functions list)

2. Go to end of function:
   Press 'End' key or scroll to last instruction

3. The bytes immediately after should be the gap
   Look for address: seg002:{gap_in_seg002_start:04X}

4. Navigate forward to: seg002:{target_in_seg002:04X}
   This is where sub_10BDB should start

5. You should see bytes starting with: 1F BE BA 43
   (pop ds; mov si, 43BAh)

SHORTCUT: Press 'G' and type: seg002:{target_in_seg002:04X}
""")

# Also calculate the call location in sub_256A3
call_offset = 0x256AD - linear_256a3  # Call is at +10 bytes
call_addr_in_seg020 = seg020_offset + call_offset

print(f"\nAlso, the CALL instruction in sub_256A3:")
print(f"  Linear: 0x{0x256AD:05X}")
print(f"  IDA: seg020:0x{call_addr_in_seg020:04X}")
print(f"  Look for: call near ptr ...")
print(f"  It should target: seg002:{target_in_seg002:04X}")
