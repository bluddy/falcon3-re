"""
Simple test - just get function info for sub_1570.
"""

import idc
import idaapi
import json

def main():
    print("="*80)
    print("Simple Test - sub_1570")
    print("="*80)
    
    try:
        idaapi.auto_wait()
        
        # Try the address
        addr = 0x1570
        print(f"Looking up address: {hex(addr)}")
        
        func = idaapi.get_func(addr)
        print(f"Function object: {func}")
        
        if func:
            result = {
                "address": hex(addr),
                "name": idc.get_func_name(addr),
                "size": func.end_ea - func.start_ea
            }
            print(f"SUCCESS: {result}")
        else:
            result = {"error": "Function not found"}
            print(f"FAILED: {result}")
        
        # Write output
        output = r"C:\Users\ybarnoy\projects\falcon3\analysis\s4\test_simple_1570.json"
        print(f"Writing to: {output}")
        
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        
        print("File written successfully")
        
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        idc.qexit(0)

if __name__ == "__main__":
    main()
