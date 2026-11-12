"""
Test IDA output file creation with absolute path.
"""

import idc
import idaapi
import json
import os

print("="*80)
print("IDA OUTPUT TEST")
print("="*80)

# Wait for auto-analysis
idaapi.auto_wait()

print(f"Current working directory: {os.getcwd()}")
print(f"IDB path: {idc.get_idb_path()}")

# Use absolute path
output_file = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\ida_output_test.json"
print(f"Output file: {output_file}")

result = {
    "test": "success",
    "cwd": os.getcwd(),
    "timestamp": "test"
}

try:
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"✓ File written successfully")
except Exception as e:
    print(f"✗ Error writing file: {e}")

# Also try in current directory
local_file = "test_local.json"
try:
    with open(local_file, "w") as f:
        json.dump({"local": "test"}, f)
    print(f"✓ Local file written: {os.path.join(os.getcwd(), local_file)}")
except Exception as e:
    print(f"✗ Error writing local file: {e}")

print("Exiting...")
idc.qexit(0)
