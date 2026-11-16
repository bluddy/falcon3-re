#!/usr/bin/env python3
"""
Test if YAML module works in IDA Python.
"""

import idc
import idaapi
import json

def main():
    idaapi.auto_wait()
    
    print("[*] Testing YAML module...")
    
    try:
        import yaml
        print("[+] yaml module imported successfully")
        
        # Try to load the enums.yaml file
        enum_path = r"C:\Users\ybarnoy\projects\falcon3\registry\enums.yaml"
        print(f"[*] Loading {enum_path}...")
        
        with open(enum_path, 'r') as f:
            enums = yaml.safe_load(f)
        
        print(f"[+] Loaded {len(enums)} enum definitions")
        print(f"[*] First enum: {enums[0]['name']}")
        
        result = {
            'yaml_available': True,
            'enums_loaded': len(enums),
            'first_enum': enums[0]['name']
        }
        
    except ImportError as e:
        print(f"[!] yaml module not available: {e}")
        result = {
            'yaml_available': False,
            'error': str(e)
        }
    except Exception as e:
        print(f"[!] Error loading YAML: {e}")
        result = {
            'yaml_available': True,
            'error': str(e)
        }
    
    # Save result
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\yaml_test_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("[+] Results saved")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
