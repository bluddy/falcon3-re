"""Minimal test to verify IDA can access the database."""
import idc
import idaapi

print("Starting minimal test...")
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete")

# Test basic function
test_addr = 0x02C527
name = idc.get_func_name(test_addr)
print(f"Function at 0x{test_addr:06X}: {name}")

print("Test complete - IDA is working!")
idc.qexit(0)
