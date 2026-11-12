#!/usr/bin/env python3
"""Verify that 0x10BDB is at seg020:051B"""

linear_10bdb = 0x10BDB
seg020_051b = 0x051B

# Calculate seg020 base
seg020_base = linear_10bdb - seg020_051b

print(f"If 0x10BDB is at seg020:0x{seg020_051b:04X}")
print(f"Then seg020 base = 0x{seg020_base:05X}")
print()

# Verify with sub_256A3
linear_256a3 = 0x256A3
calc_offset = linear_256a3 - seg020_base

print(f"Verification with sub_256A3:")
print(f"  Linear: 0x{linear_256a3:05X}")
print(f"  Calculated offset in seg020: 0x{calc_offset:04X}")
print(f"  Observed in IDA: seg020:5FED")
print(f"  Match: {'YES' if calc_offset == 0x5FED else 'NO'}")

if calc_offset == 0x5FED:
    print("\nCORRECT! 0x10BDB is at seg020:051B")
    print()
    print("The call in sub_256A3 at seg020:5FF7 should target seg020:051B")
