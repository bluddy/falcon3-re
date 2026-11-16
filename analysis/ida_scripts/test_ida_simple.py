"""
Simple test to verify IDA scripting works.
"""
import idc
import idaapi

def main():
    print("=== IDA SIMPLE TEST ===")
    print("Starting test...")
    
    # Wait for auto-analysis
    idaapi.auto_wait()
    print("Auto-analysis complete")
    
    # Get some basic info
    info = idaapi.get_inf_structure()
    print(f"Database: {idaapi.get_root_filename()}")
    print(f"Min EA: 0x{info.min_ea:X}")
    print(f"Max EA: 0x{info.max_ea:X}")
    
    # Try to get an enum
    enum_id = idc.get_enum("PilotRank")
    if enum_id != idc.BADADDR:
        print(f"Found enum PilotRank: ID={enum_id}")
    else:
        print("Enum PilotRank not found")
    
    # Try to get a struct
    sid = idc.get_struc_id("PilotRecord")
    if sid != idc.BADADDR:
        print(f"Found struct PilotRecord: ID={sid}")
    else:
        print("Struct PilotRecord not found")
    
    print("Test complete!")
    
    # Save output to file
    with open(r"C:\Users\ybarnoy\projects\falcon3\analysis\ida_test_output.txt", 'w') as f:
        f.write("IDA test completed successfully\n")
        f.write(f"Database: {idaapi.get_root_filename()}\n")
    
    print("Output saved to analysis/ida_test_output.txt")
    
    # Exit
    idc.qexit(0)

if __name__ == "__main__":
    main()
