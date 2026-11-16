"""
Test script to verify IDA automation is working.
"""

import idc
import idautils
import json

print("=" * 60)
print("IDA Test Script Starting...")
print("=" * 60)

# Get basic info
db_path = idc.get_idb_path()
print(f"Database: {db_path}")

# Count functions
func_count = 0
for func_ea in idautils.Functions():
    func_count += 1
    if func_count >= 10:
        break

print(f"Found at least {func_count} functions")

# Test renaming on a copy
test_ea = 0x13DD40
old_name = idc.get_func_name(test_ea)
print(f"\nTest function at 0x{test_ea:06X}: {old_name}")

# Write results to file
output = {
    'status': 'success',
    'db_path': db_path,
    'func_count': func_count,
    'test_ea': test_ea,
    'test_name': old_name
}

output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_test_result.json'
with open(output_file, 'w') as f:
    json.dump(output, f, indent=2)

print(f"\n✓ Results written to: {output_file}")
print("=" * 60)
print("IDA Test Script Complete")
print("=" * 60)

idc.qexit(0)
