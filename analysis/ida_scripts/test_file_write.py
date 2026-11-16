import idc
import idaapi
import json

# Wait for autoanalysis
idaapi.auto_wait()

# Test basic file write
test_data = {"test": "success", "message": "File write works"}

output_path = r'C:\Users\ybarnoy\projects\falcon3\analysis\test_output.json'

print(f"Attempting to write to: {output_path}")

try:
    with open(output_path, 'w') as f:
        json.dump(test_data, f, indent=2)
    print(f"SUCCESS: File written to {output_path}")
except Exception as e:
    print(f"ERROR: {e}")
    # Try alternative location
    alt_path = r'C:\Users\ybarnoy\test_output.json'
    print(f"Trying alternative: {alt_path}")
    with open(alt_path, 'w') as f:
        json.dump(test_data, f, indent=2)
    print(f"Alternative succeeded: {alt_path}")

idc.qexit(0)
