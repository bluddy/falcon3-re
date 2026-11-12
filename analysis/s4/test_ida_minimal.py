"""
Minimal IDA test - just verify basic functionality and exit quickly.
"""

import idc
import idaapi
import json
from pathlib import Path

print("="*80)
print("MINIMAL IDA TEST")
print("="*80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete")

# Basic info
print(f"\nIDA version: {idaapi.get_kernel_version()}")
print(f"Database: {idc.get_idb_path()}")

# Test basic operations
print("\nTesting basic operations...")

# 1. Get a function
addr = idc.get_name_ea_simple("view_projection")
if addr != idc.BADADDR:
    print(f"✓ Found view_projection at {hex(addr)}")
    func = idaapi.get_func(addr)
    if func:
        print(f"✓ Got function object, size = {func.end_ea - func.start_ea} bytes")
else:
    print("✗ view_projection not found")

# 2. Test DGROUP
dgroup_base = idc.get_segm_start(idc.get_segm_by_name("DGROUP"))
if dgroup_base != idc.BADADDR:
    print(f"✓ Found DGROUP at {hex(dgroup_base)}")
else:
    print("✗ DGROUP not found")

# Save minimal result
result = {
    "test": "success",
    "view_projection": hex(addr) if addr != idc.BADADDR else None,
    "dgroup_base": hex(dgroup_base) if dgroup_base != idc.BADADDR else None
}

output_file = Path(__file__).parent / "ida_test_result.json"
with open(output_file, "w") as f:
    json.dump(result, f, indent=2)

print(f"\n✓ Test complete, saved to {output_file}")
print("Exiting IDA...")

# Exit immediately
idc.qexit(0)
