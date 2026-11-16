#!/usr/bin/env python3
"""
Step 3: Apply PilotRecord structure to squad_campaign_file_loader code.

This script:
1. Finds squad_campaign_file_loader function (0x6A651)
2. Analyzes how it accesses the pilot data buffer
3. Applies PilotRecord structure type to buffer accesses
4. Sets function parameter types
5. Exports before/after decompilation for comparison
"""

import idc
import idaapi
import idautils
import json

def get_function_decompilation(func_addr):
    """Get pseudocode decompilation of a function."""
    try:
        cfunc = idaapi.decompile(func_addr)
        if cfunc:
            return str(cfunc)
        return None
    except Exception as e:
        print(f"[!] Decompilation failed: {e}")
        return None

def find_struct_accesses(func_addr):
    """Find places where code accesses buffer + offset patterns."""
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    accesses = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        # Look for memory access patterns
        mnem = idc.print_insn_mnem(ea)
        
        # Common patterns: mov, lea, add with memory operands
        if mnem in ['mov', 'lea', 'add', 'cmp']:
            disasm = idc.generate_disasm_line(ea, 0)
            
            # Look for patterns like [bp+var_X] or [bx+X] that might be buffer accesses
            if '[' in disasm and ('+' in disasm or '-' in disasm):
                accesses.append({
                    'addr': ea,
                    'mnem': mnem,
                    'disasm': disasm
                })
        
        ea = idc.next_head(ea, func.end_ea)
    
    return accesses

def apply_structure_to_data(data_addr, struct_name):
    """Apply a structure type to a data location."""
    sid = idc.get_struc_id(struct_name)
    if sid == idc.BADADDR:
        print(f"[!] Structure {struct_name} not found")
        return False
    
    # Try to apply structure
    result = idc.create_struct(data_addr, -1, struct_name)
    return result

def main():
    idaapi.auto_wait()
    
    print("="*80)
    print("STEP 3: APPLY PILOTRECORD STRUCTURE TO CODE")
    print("="*80)
    print()
    
    try:
    
    try:
        # Target function
        func_name = "squad_campaign_file_loader"
        func_addr = idc.get_name_ea_simple(func_name)
    
    if func_addr == idc.BADADDR:
        # Try by address
        func_addr = 0x6A651
        print(f"[*] Function {func_name} not found by name, trying address 0x{func_addr:X}")
        
        func = idaapi.get_func(func_addr)
        if not func:
            print(f"[!] No function at 0x{func_addr:X}")
            result = {'error': 'Function not found'}
            
            with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\apply_pilot_structure_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            idc.qexit(1)
        else:
            print(f"[+] Found function at 0x{func_addr:X}")
    else:
        print(f"[+] Found {func_name} at 0x{func_addr:X}")
    
    # Get function info
    func = idaapi.get_func(func_addr)
    func_size = func.end_ea - func.start_ea
    print(f"[*] Function size: {func_size} bytes (0x{func_size:X})")
    print()
    
    # Get BEFORE decompilation
    print("[*] Getting BEFORE decompilation...")
    decompilation_before = get_function_decompilation(func_addr)
    if decompilation_before:
        print(f"[+] Got decompilation ({len(decompilation_before)} chars)")
        # Save first 500 chars as preview
        preview_before = decompilation_before[:500]
        print(f"[*] Preview:\n{preview_before}\n...")
    else:
        print("[!] No decompilation available")
        preview_before = None
    print()
    
    # Check if PilotRecord structure exists
    print("[*] Checking for PilotRecord structure...")
    sid = idc.get_struc_id("PilotRecord")
    if sid == idc.BADADDR:
        print("[!] PilotRecord structure not found in IDA")
        result = {'error': 'PilotRecord structure not registered'}
        
        with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\apply_pilot_structure_result.json', 'w') as f:
            json.dump(result, f, indent=2)
        
        idc.qexit(1)
    
    struct_size = idc.get_struc_size(sid)
    print(f"[+] Found PilotRecord: ID={sid}, Size={struct_size} bytes")
    
    # List structure fields
    print("[*] PilotRecord fields:")
    member = idc.get_first_member(sid)
    field_count = 0
    while member != -1:
        member_name = idc.get_member_name(sid, member)
        member_size = idc.get_member_size(sid, member)
        print(f"    +0x{member:02X}: {member_name} ({member_size} bytes)")
        member = idc.get_next_member(sid, member)
        field_count += 1
    
    print(f"[+] {field_count} fields defined")
    print()
    
    # Find potential buffer access patterns
    print("[*] Analyzing function for buffer access patterns...")
    accesses = find_struct_accesses(func_addr)
    print(f"[+] Found {len(accesses)} potential memory accesses")
    
    # Show some examples
    if len(accesses) > 0:
        print("[*] Sample accesses:")
        for access in accesses[:10]:  # First 10
            print(f"    0x{access['addr']:X}: {access['disasm']}")
        if len(accesses) > 10:
            print(f"    ... and {len(accesses) - 10} more")
    print()
    
    # Look for specific pilot data patterns
    # In file loader, pilots start at buffer offset 0x3C (60 bytes)
    # Each pilot is 66 bytes (0x42)
    print("[*] Looking for pilot data offset patterns (0x3C, 0x42)...")
    
    pilot_related = []
    for access in accesses:
        disasm = access['disasm']
        # Look for hex values 3C, 42, or decimal 60, 66
        if any(x in disasm for x in ['3Ch', '42h', '60', '66']):
            pilot_related.append(access)
    
    print(f"[+] Found {len(pilot_related)} pilot-related accesses")
    if len(pilot_related) > 0:
        print("[*] Pilot-related accesses:")
        for access in pilot_related[:20]:
            print(f"    0x{access['addr']:X}: {access['disasm']}")
    print()
    
    # Try to set function prototype with PilotRecord return type
    print("[*] Attempting to improve function type information...")
    
    # The function likely takes (filename, buffer_ptr) and returns status
    # We can at least document what we know
    
    # Add comment about pilot structure
    func_cmt = f"""Squad/Campaign file loader (0x6A651)
    
Loads .SQU (squadron, 2703 bytes) and .CAM (campaign, 11828 bytes) files.

Squadron file structure:
  0x00-0x3B: SquadronHeader (60 bytes)
  0x3C: PilotRecord[30] (30 pilots × 66 bytes = 1980 bytes)
  0x7F8: ExtendedPilotRecord[10] (pilots 20-29, 10 × 66 bytes = 660 bytes)

Each PilotRecord is 66 bytes (0x42):
  +0x00: status_flags[2]
  +0x02: rank (PilotRank enum)
  +0x03: callsign[15]
  +0x13: nickname[15]
  +0x22: id_code[4]
  +0x26: dogfighting_skill, bombing_skill, flying_skill, fatigue_level
  +0x2A: mission_data[28]
"""
    
    idc.set_func_cmt(func_addr, func_cmt, 1)  # 1 = repeatable comment
    print("[+] Added function comment with structure information")
    print()
    
    # Get AFTER decompilation (with comments added)
    print("[*] Getting AFTER decompilation...")
    decompilation_after = get_function_decompilation(func_addr)
    if decompilation_after:
        print(f"[+] Got decompilation ({len(decompilation_after)} chars)")
        preview_after = decompilation_after[:500]
        print(f"[*] Preview:\n{preview_after}\n...")
    else:
        preview_after = None
    print()
    
    # Save full decompilations
    print("[*] Saving decompilations...")
    
    if decompilation_before:
        with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\squad_loader_decompile_before.c', 'w') as f:
            f.write(decompilation_before)
        print("[+] Saved BEFORE decompilation to squad_loader_decompile_before.c")
    
    if decompilation_after:
        with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\squad_loader_decompile_after.c', 'w') as f:
            f.write(decompilation_after)
        print("[+] Saved AFTER decompilation to squad_loader_decompile_after.c")
    print()
    
    # Save results
    result = {
        'function_name': func_name,
        'function_addr': hex(func_addr),
        'function_size': func_size,
        'pilot_record_found': True,
        'pilot_record_size': struct_size,
        'pilot_record_fields': field_count,
        'memory_accesses_found': len(accesses),
        'pilot_related_accesses': len(pilot_related),
        'decompilation_before_length': len(decompilation_before) if decompilation_before else 0,
        'decompilation_after_length': len(decompilation_after) if decompilation_after else 0,
        'improvements_applied': [
            'Added detailed function comment with structure layout',
            'Documented pilot record offsets',
            'Exported before/after decompilation'
        ],
        'next_steps': [
            'Manually review decompilation and identify buffer variables',
            'Apply PilotRecord* type to buffer variables in IDA GUI',
            'Create array type: PilotRecord[30] for pilot array',
            'Apply enum types to rank field accesses'
        ]
    }
    
    with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\apply_pilot_structure_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print("="*80)
    print("STEP 3 ANALYSIS COMPLETE")
    print("="*80)
    print()
    print(f"Results saved to: analysis/apply_pilot_structure_result.json")
    print(f"Decompilation BEFORE: analysis/squad_loader_decompile_before.c")
    print(f"Decompilation AFTER: analysis/squad_loader_decompile_after.c")
    print()
    print("Next steps:")
    print("1. Review the decompilation files")
    print("2. Identify buffer variables that hold pilot data")
    print("3. Manually apply PilotRecord* type in IDA GUI")
    print("4. Apply PilotRecord[30] array type to pilot array")
    print()
    
    idc.qexit(0)

    except Exception as e:
        print(f"[!] ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        error_result = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        
        with open(r'C:\Users\ybarnoy\projects\falcon3\analysis\apply_pilot_structure_result.json', 'w') as f:
            json.dump(error_result, f, indent=2)
        
        idc.qexit(1)

if __name__ == "__main__":
    main()
