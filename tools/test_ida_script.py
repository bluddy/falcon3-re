"""Simple test script to verify IDA Python environment."""

import idaapi
import idc
import json

print("=" * 60)
print("IDA Python Test Script")
print("=" * 60)

try:
    # Wait for analysis
    idaapi.auto_wait()
    
    # Get basic info
    info = {
        'idb_path': idc.get_idb_path(),
        'input_file': idaapi.get_input_file_path(),
        'function_count': len(list(idautils.Functions())) if 'idautils' in dir() else 'N/A',
    }
    
    print("\n✓ IDA API accessible")
    print(f"  IDB: {info['idb_path']}")
    print(f"  Input: {info['input_file']}")
    
    # Try to write a file
    import os
    idb_dir = os.path.dirname(info['idb_path'])
    test_file = os.path.join(idb_dir, 'test_output.json')
    
    with open(test_file, 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"\n✓ File write successful: {test_file}")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

idc.qexit(0)
