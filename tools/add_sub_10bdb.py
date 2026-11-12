#!/usr/bin/env python3
"""
Add missing function sub_10BDB to IDA database.

Finding 207: sub_10BDB is called 10,222 times but doesn't exist in IDB.
It's in a 149-byte gap starting at 0x10BDB.

This script:
1. Creates instructions at 0x10BDB
2. Creates a function
3. Finds the function end (retf or next call target)
4. Verifies xrefs
5. Exports updated function_bytes.json
"""
import idc
import idaapi
import idautils
import json
from pathlib import Path

print("="*80)
print("ADDING MISSING FUNCTION sub_10BDB TO IDB")
print("="*80)

# Target address
target_ea = 0x10BDB

print(f"\nTarget address: 0x{target_ea:05X}")

# Step 1: Check if already exists
existing_func = idaapi.get_func(target_ea)
if existing_func:
    print(f"WARNING: Function already exists at 0x{target_ea:05X}")
    print(f"  Start: 0x{existing_func.start_ea:05X}")
    print(f"  End: 0x{existing_func.end_ea:05X}")
    print(f"  Size: {existing_func.end_ea - existing_func.start_ea} bytes")
    print("\nSkipping creation (already done)")
else:
    print(f"Confirmed: No function at 0x{target_ea:05X}")
    
    # Step 2: Ensure instructions are created
    print(f"\nStep 1: Creating instructions starting at 0x{target_ea:05X}...")
    
    # Create instructions up to 64 bytes or until we hit retf/existing code
    created_count = 0
    ea = target_ea
    for i in range(64):
        if idc.is_code(idc.get_full_flags(ea)):
            # Already code, skip
            ea = idc.next_head(ea, target_ea + 64)
            if ea == idaapi.BADADDR:
                break
            continue
        
        # Try to create instruction
        insn_len = idc.create_insn(ea)
        if insn_len > 0:
            created_count += 1
            ea += insn_len
        else:
            print(f"  Failed to create instruction at 0x{ea:05X}")
            break
        
        # Check if we hit a return
        mnem = idc.print_insn_mnem(ea - insn_len)
        if mnem in ['retf', 'ret', 'retn']:
            print(f"  Found {mnem} at 0x{ea - insn_len:05X}")
            break
    
    print(f"  Created/verified {created_count} instructions")
    
    # Step 3: Create function
    print(f"\nStep 2: Creating function at 0x{target_ea:05X}...")
    
    result = idc.add_func(target_ea)
    if result:
        print(f"  ✓ Function created successfully")
    else:
        print(f"  ✗ Failed to create function")
        print(f"  Trying with explicit end...")
        
        # Find end manually
        ea = target_ea
        for i in range(100):
            mnem = idc.print_insn_mnem(ea)
            if mnem in ['retf', 'ret', 'retn']:
                func_end = idc.next_head(ea, idaapi.BADADDR)
                result = idc.add_func(target_ea, func_end)
                if result:
                    print(f"  ✓ Function created with explicit end 0x{func_end:05X}")
                else:
                    print(f"  ✗ Still failed with explicit end")
                break
            ea = idc.next_head(ea, idaapi.BADADDR)
            if ea == idaapi.BADADDR:
                break

# Step 4: Verify and analyze the function
print(f"\nStep 3: Verifying function...")
func = idaapi.get_func(target_ea)
if func:
    print(f"  ✓ Function exists")
    print(f"  Start: 0x{func.start_ea:05X}")
    print(f"  End: 0x{func.end_ea:05X}")
    print(f"  Size: {func.end_ea - func.start_ea} bytes")
    
    # Get function name
    func_name = idc.get_func_name(target_ea)
    print(f"  Name: {func_name}")
    
    # Check xrefs TO this function
    print(f"\n  Xrefs TO this function:")
    xrefs_to = list(idautils.XrefsTo(target_ea))
    if xrefs_to:
        print(f"    Found {len(xrefs_to)} xrefs")
        for xref in xrefs_to[:10]:
            caller_name = idc.get_func_name(xref.frm)
            print(f"      0x{xref.frm:05X} from {caller_name} (type {xref.type})")
    else:
        print(f"    WARNING: No xrefs found!")
        print(f"    Expected: sub_256A3 at 0x256AD should call this")
    
    # Disassemble first few instructions
    print(f"\n  Disassembly (first 10 lines):")
    ea = func.start_ea
    for i in range(10):
        if ea >= func.end_ea:
            break
        disasm = idc.generate_disasm_line(ea, 0)
        print(f"    0x{ea:05X}  {disasm}")
        ea = idc.next_head(ea, func.end_ea)
        if ea == idaapi.BADADDR:
            break
    
    print(f"\nStep 4: Checking caller (sub_256A3)...")
    
    # Verify sub_256A3 calls this
    caller_ea = 0x256A3
    caller_func = idaapi.get_func(caller_ea)
    if caller_func:
        print(f"  ✓ Caller function exists at 0x{caller_ea:05X}")
        
        # Check xrefs FROM caller
        xrefs_from = list(idautils.XrefsFrom(caller_ea))
        calls_10bdb = any(xref.to == target_ea for xref in xrefs_from)
        
        if calls_10bdb:
            print(f"  ✓ sub_256A3 shows xref to sub_10BDB")
        else:
            print(f"  ⚠ sub_256A3 doesn't show direct xref")
            print(f"    (May need to reanalyze caller)")
            
            # Check call instruction at expected offset
            call_ea = caller_ea + 10  # Offset where call should be
            if idc.is_code(idc.get_full_flags(call_ea)):
                mnem = idc.print_insn_mnem(call_ea)
                op = idc.print_operand(call_ea, 0)
                print(f"    Instruction at +10: {mnem} {op}")
    else:
        print(f"  ✗ Caller function not found")

else:
    print(f"  ✗ Function does NOT exist after creation attempt")
    print(f"  Manual intervention required")

# Step 5: Save database
print(f"\nStep 5: Saving IDA database...")
idaapi.save_database(idc.get_idb_path(), 0)
print(f"  ✓ Database saved")

# Step 6: Export function_bytes.json
print(f"\nStep 6: Exporting function_bytes.json...")

output_path = Path(idc.get_idb_path()).parent / "function_bytes.json"
print(f"  Output: {output_path}")

# Export all functions
functions_data = {}
for func_ea in idautils.Functions():
    func = idaapi.get_func(func_ea)
    if not func:
        continue
    
    func_name = idc.get_func_name(func_ea)
    func_size = func.end_ea - func.start_ea
    
    # Get bytes
    func_bytes = idc.get_bytes(func.start_ea, func_size)
    if func_bytes:
        bytes_hex = func_bytes.hex()
    else:
        bytes_hex = ""
    
    # Check if far function
    flags = idc.get_func_attr(func.start_ea, idc.FUNCATTR_FLAGS)
    is_far = bool(flags & idc.FUNC_FAR) if flags != -1 else False
    
    # Check if overlay (ea >= 0x1FBC0)
    is_overlay = func.start_ea >= 0x1FBC0
    
    functions_data[func_name] = {
        'ea': func.start_ea,
        'size': func_size,
        'bytes': bytes_hex,
        'is_far': is_far,
        'overlay': is_overlay,
        'name': func_name
    }

# Write JSON
with open(output_path, 'w') as f:
    json.dump(functions_data, f, indent=1)

print(f"  ✓ Exported {len(functions_data)} functions")

# Check if sub_10BDB is in export
if 'sub_10BDB' in functions_data:
    print(f"  ✓ sub_10BDB is in export")
    print(f"    Size: {functions_data['sub_10BDB']['size']} bytes")
    print(f"    Bytes: {functions_data['sub_10BDB']['bytes'][:40]}...")
else:
    print(f"  ⚠ sub_10BDB NOT in export (may have different name)")
    # Check by address
    for name, data in functions_data.items():
        if data['ea'] == target_ea:
            print(f"    Found at 0x{target_ea:05X} as: {name}")
            break

print(f"\n" + "="*80)
print("COMPLETE")
print("="*80)
print(f"\nNext steps:")
print(f"  1. Verify sub_10BDB in function_bytes.json")
print(f"  2. Analyze disassembly to understand function")
print(f"  3. Name the function based on purpose")
print(f"  4. Complete DGROUP:0x4287 analysis")

idc.qexit(0)
