#!/usr/bin/env python3
"""
Calculate segment:offset for IDA address 0x10BDB.

IDA uses linear addresses (0x10000 base).
Real mode segment:offset format varies by segment.
"""

ida_addr = 0x10BDB

print("="*80)
print("SEGMENT:OFFSET CALCULATION FOR 0x10BDB")
print("="*80)

print(f"\nIDA linear address: 0x{ida_addr:05X}")

# IDA load base is 0x10000
# File offset = IDA address - 0x10000 + 0x2C00 (header size)
file_offset = ida_addr - 0x10000 + 0x2C00
print(f"File offset: 0x{file_offset:05X}")

# Now we need to find which segment this belongs to
# Check against known segments from FALCONCD.EXE.yaml

# Resident code segments:
segments = [
    ("seg005", 0x11BA0, 0x168E0, "0x05BA"),
    ("seg020", 0x1F6C0, 0x2AA30, "0x1F6C"),  # Main resident
]

# Check which segment contains 0x10BDB
print(f"\nChecking segment membership:")

# 0x10BDB is before seg005 starts (0x11BA0)
# This is in the early part of the executable

# For addresses below seg005, they're typically in the entry segment
# Entry linear segment in MZ files starts at 0x10000

# Calculate as if it's in the initial code segment
# For early code: segment = (ida_addr - 0x10000) / 16 (paragraph alignment)
# But IDA might show this differently

print(f"\n0x10BDB is in EARLY resident code (before seg005)")
print(f"This is typically shown as:")

# Method 1: As offset from image base
offset_from_base = ida_addr - 0x10000
para = offset_from_base // 16
off = offset_from_base % 16
print(f"  Paragraph: 0x{para:04X}, Offset: 0x{off:X}")

# Method 2: Likely actual segment in IDA
# Early code is often in segment starting around 0x10B0 or similar
# Let's check what IDA might use

print(f"\nLikely IDA representations:")
print(f"  1. Linear address: 0x10BDB (type: 10BDB)")
print(f"  2. Segment 0x10B0, offset 0xDB (type: 10B0:00DB)")
print(f"  3. Segment 0x10BD, offset 0xB (type: 10BD:000B)")

# The most likely is that IDA shows this in segment 0x10BD
seg_candidate_1 = 0x10BD
off_candidate_1 = 0xB

# Verify: seg * 16 + offset + 0x10000 = 0x10BDB
verify_1 = seg_candidate_1 * 16 + off_candidate_1 + 0x10000
print(f"\nVerification 1: 0x{seg_candidate_1:04X}:0x{off_candidate_1:03X}")
print(f"  -> 0x{verify_1:05X} {'OK' if verify_1 == ida_addr else 'NO'}")

# Or it might be shown as offset within a larger segment
# Check if IDA has a segment that starts earlier

# Common pattern: segment 0x1000, offset 0xBDB
seg_candidate_2 = 0x1000
off_candidate_2 = 0xBDB

verify_2 = seg_candidate_2 * 16 + off_candidate_2 + 0x10000
print(f"\nVerification 2: 0x{seg_candidate_2:04X}:0x{off_candidate_2:04X}")
print(f"  -> 0x{verify_2:05X} {'OK' if verify_2 == ida_addr else 'NO'}")

# The actual segment IDA uses depends on how it set up the segments
# Let's check what segment name IDA might show

print(f"\n" + "="*80)
print("RECOMMENDATION FOR IDA NAVIGATION")
print("="*80)

print(f"""
In IDA, try these methods to navigate to 0x10BDB:

Method 1: Jump to linear address
  Press 'G'
  Type: 10BDB
  Press Enter
  
  If this jumps somewhere else, IDA might be interpreting it as segment:offset

Method 2: Jump with explicit format  
  Press 'G'
  Try these variations:
    - 0x10BDB
    - 0000:10BDB
    - .text:00010BDB (if .text segment exists)

Method 3: From Functions window
  View -> Open Subviews -> Functions
  Look for functions near 0x10BDB:
    - sub_10B1C should end around 0x10B46
    - Next function after gap
  Navigate to end of sub_10B1C
  Page down to see the gap where 0x10BDB should be

Method 4: From sub_256A3 (the caller)
  Press 'G', type: 256A3
  Find the call instruction around offset +10
  It should be: call near sub_10BDB or call 10BDBh
  Double-click on the call target to jump there

Method 5: Search for the bytes
  Alt+B (Search -> Sequence of bytes)
  Enter: 1F BE BA 43
  These are the first 4 bytes at 0x10BDB:
    1F = pop ds
    BE BA 43 = mov si, 43BAh

Method 6: Check current segment scheme
  Look at what IDA shows in the segment register display
  If you're at another address, note the segment:offset format
  Then calculate accordingly
""")

print("\nIf you're at 0x256A3 (sub_256A3), the call to 0x10BDB is at offset +10")
print("The call instruction bytes are: E8 2B B5 (call near with relative offset)")
