"""Test simple rename to verify IDA is working."""

import idc
import idaapi

def main():
    idaapi.auto_wait()
    
    print("Testing rename...")
    
    # Test rename word_79F16
    addr = 0x79F16
    old_name = idc.get_name(addr)
    print(f"Old name at 0x{addr:X}: {old_name}")
    
    result = idc.set_name(addr, "current_view_index", idc.SN_NOWARN | idc.SN_NOCHECK)
    print(f"Rename result: {result}")
    
    new_name = idc.get_name(addr)
    print(f"New name: {new_name}")
    
    # Save output
    with open(r"c:\Users\ybarnoy\projects\falcon3\analysis\dgroup\test_rename_output.txt", 'w') as f:
        f.write(f"Old: {old_name}\n")
        f.write(f"New: {new_name}\n")
        f.write(f"Result: {result}\n")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
