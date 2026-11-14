#!/usr/bin/env python3
"""
Direct application of 6 REBASE fixes for Finding 205.
Bypasses the manifest system for simplicity.
"""
import ida_bytes
import ida_funcs
import ida_name
import ida_segregs
import ida_segment
import ida_ua
import idaapi
import idc
import idautils

# The 6 REBASE targets for Finding 205
# Format: (old_start, new_start, end, name)
REBASES = [
    (0x407BF, 0x407BE, 0x40843, "sub_407BF"),
    (0x40DDB, 0x40DDA, 0x40E35, "sub_40DDB"),
    (0x40C69, 0x40C68, 0x40C73, "sub_40C69"),
    (0x40045, 0x40044, 0x4005C, "sub_40045"),
    (0x3FD66, 0x3FD65, 0x3FD89, "sub_3FD66"),
    (0x404F1, 0x404F0, 0x404F6, "sub_404F1"),
]

def descend(ea, lo, hi, made):
    """Recursive descent disassembly (from apply_orphan_funcs.py)"""
    if ea in made or not (lo <= ea < hi):
        return
    made.add(ea)
    if not ida_ua.create_insn(ea):
        return
    insn = idautils.DecodeInstruction(ea)
    if insn:
        for op in insn.ops:
            if op.type == idaapi.o_near:
                descend(op.addr, lo, hi, made)

def rebase_function(old_start, new_start, end, name):
    """
    Create a function at new_start (1 byte before old_start).
    Since these are currently unexplored bytes, we need to:
    1. Clear any existing items in [new_start, end)
    2. Recursive descent from new_start to decode instructions
    3. Create function [new_start, end)
    """
    print(f"\n=== CREATE {name}: 0x{new_start:X} - 0x{end:X} ({end-new_start} bytes) ===")
    
    # Check if function already exists anywhere in this range
    for ea in range(new_start, end):
        f = ida_funcs.get_func(ea)
        if f:
            print(f"  WARNING: Function already exists at 0x{f.start_ea:X}")
            if f.start_ea == new_start and f.end_ea == end:
                print(f"  ✓ Already correct - skipping")
                return True
            else:
                print(f"  Deleting existing function first")
                ida_funcs.del_func(f.start_ea)
                break
    
    # 1. Delete any existing items in range
    ida_bytes.del_items(new_start, ida_bytes.DELIT_SIMPLE, end - new_start)
    print(f"  Cleared items in [0x{new_start:X}, 0x{end:X})")
    
    # 2. Recursive descent from new_start to decode instructions
    made = set()
    descend(new_start, new_start, end, made)
    print(f"  Decoded {len(made)} instructions")
    
    if len(made) == 0:
        print(f"  ERROR: Failed to decode any instructions")
        return False
    
    # 3. Create function at new_start
    if not ida_funcs.add_func(new_start, end):
        print(f"  ERROR: Failed to create function at 0x{new_start:X}")
        return False
    print(f"  Created function at 0x{new_start:X}")
    
    # 4. Set far flag (assume far for R05 overlay functions)
    f = ida_funcs.get_func(new_start)
    if f:
        f.flags |= ida_funcs.FUNC_FAR
        ida_funcs.update_func(f)
    
    # 5. Set name if meaningful
    if name and not name.startswith("sub_"):
        ida_name.set_name(new_start, name, ida_name.SN_NOWARN)
    
    # Verify
    f_new = ida_funcs.get_func(new_start)
    if f_new and f_new.start_ea == new_start and f_new.end_ea == end:
        actual_name = idc.get_func_name(new_start)
        print(f"  ✓ SUCCESS: {actual_name} at 0x{new_start:X} - 0x{end:X}")
        return True
    else:
        print(f"  ERROR: Verification failed")
        return False

def main():
    """Apply all 6 REBASEs"""
    log_path = "C:/Users/ybarnoy/projects/falcon3/analysis/s1/rebase_apply_205.log"
    
    with open(log_path, "w") as log:
        import sys
        sys.stdout = log
        sys.stderr = log
        
        print("=" * 60)
        print("Finding 205: P2 batch 1 - 6 not_head fixes")
        print("Creating functions at correct addresses")
        print("=" * 60)
        
        success_count = 0
        for old_start, new_start, end, name in REBASES:
            if rebase_function(old_start, new_start, end, name):
                success_count += 1
        
        print("\n" + "=" * 60)
        print(f"Results: {success_count}/{len(REBASES)} successful")
        print("=" * 60)
        
        if success_count == len(REBASES):
            print("\n✓ All functions created successfully!")
            print("\nSaving IDB...")
            # Save the IDB
            import ida_loader
            ida_loader.save_database(ida_nalt.get_idb_path(), ida_loader.DBFL_COMP)
            print("✓ IDB saved")
        else:
            print(f"\n✗ {len(REBASES) - success_count} functions failed")
            print("NOT saving IDB")
        
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
    
    print(f"Logged to {log_path}")

if __name__ == "__main__":
    main()
    idc.qexit(0)
