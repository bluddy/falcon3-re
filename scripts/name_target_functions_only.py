import idc
import idaapi
import sys

output_file = open(r"C:\Users\ybarnoy\projects\falcon3\target_func_naming.txt", "w")
sys.stdout = output_file
sys.stderr = output_file

print("Starting target function naming...")
idaapi.auto_wait()

# Function naming only - most critical
functions = [
    (0x32D22, "mission_state_initializer", "Initializes mission state and objectives (850B)"),
    (0x3E96F, "ai_target_priority_evaluator", "Evaluates target priority for AI, checks 11 target count fields [di+0xB3-0xBF] (479B)"),
    (0x4478D, "farobj_slot_target_search", "Searches entity slots for valid targets (222B)"),
    (0x48B05, "target_cycle_scan", "Scans entities for HUD target cycling (283B)"),
    (0x48C20, "target_processing_helper", "Helper function for target processing"),
]

print("=== NAMING FUNCTIONS ===\n")
success = 0
failed = 0

for addr, name, comment in functions:
    try:
        # Check if function exists
        func = idaapi.get_func(addr)
        if not func:
            print(f"✗ No function at 0x{addr:X}")
            failed += 1
            continue
        
        # Set name
        if idc.set_name(addr, name, idc.SN_CHECK):
            print(f"✓ 0x{addr:X} -> {name}")
            success += 1
            # Set comment
            idc.set_func_cmt(addr, comment, 0)
            print(f"  {comment}")
        else:
            existing = idc.get_name(addr)
            print(f"✗ Failed 0x{addr:X} (existing: {existing})")
            failed += 1
    except Exception as e:
        print(f"✗ Exception at 0x{addr:X}: {e}")
        failed += 1
    print()

print(f"\nSummary: {success} succeeded, {failed} failed")
print("\nFunction naming complete.")
output_file.close()
idc.qexit(0)
