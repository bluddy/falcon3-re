"""
Analyze key entity update functions to understand their true purpose.

Functions to analyze:
1. farobj_slot_update_driver @ 0x3C1BD (348 bytes) - Main coordinator?
2. farobj_step_terrain_clamp @ 0x47787 (234 bytes) - Ground collision?
3. ai_entity_update_step @ 0x3D37F (1319 bytes) - AI/physics/combat?
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("ENTITY UPDATE FUNCTION ANALYSIS")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

results = {}

# Function 1: farobj_slot_update_driver @ 0x3C1BD
print("=" * 80)
print("ANALYZING: farobj_slot_update_driver @ 0x3C1BD")
print("=" * 80)

func_ea = 0x3C1BD
func = idaapi.get_func(func_ea)

if func:
    func_name = idc.get_func_name(func_ea)
    print(f"Function: {func_name}")
    print(f"Size: {func.end_ea - func.start_ea} bytes\n")
    
    # Get full disassembly
    disasm_lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({
            'address': hex(ea),
            'disasm': disasm
        })
        ea = idc.next_head(ea, func.end_ea)
    
    # Find all function calls
    print("Function calls made:")
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        insn = idaapi.insn_t()
        insn_len = idaapi.decode_insn(insn, ea)
        
        if insn_len > 0 and insn.itype == idaapi.NN_call:
            target = insn.ops[0]
            if target.type == idaapi.o_near:
                target_ea = target.addr
                target_name = idc.get_func_name(target_ea)
                if target_name:
                    calls.append({
                        'address': hex(ea),
                        'target': hex(target_ea),
                        'function': target_name
                    })
                    print(f"  {ea:#08x} -> {target_name}")
        
        ea = idc.next_head(ea, func.end_ea)
    
    results['farobj_slot_update_driver'] = {
        'address': hex(func_ea),
        'size': func.end_ea - func.start_ea,
        'calls': calls,
        'disassembly': disasm_lines
    }
    
    print(f"\nTotal calls: {len(calls)}")

# Function 2: farobj_step_terrain_clamp @ 0x47787
print(f"\n{'=' * 80}")
print("ANALYZING: farobj_step_terrain_clamp @ 0x47787")
print("=" * 80)

func_ea = 0x47787
func = idaapi.get_func(func_ea)

if func:
    func_name = idc.get_func_name(func_ea)
    print(f"Function: {func_name}")
    print(f"Size: {func.end_ea - func.start_ea} bytes\n")
    
    # Get full disassembly
    disasm_lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({
            'address': hex(ea),
            'disasm': disasm
        })
        ea = idc.next_head(ea, func.end_ea)
    
    # Find all function calls
    print("Function calls made:")
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        insn = idaapi.insn_t()
        insn_len = idaapi.decode_insn(insn, ea)
        
        if insn_len > 0 and insn.itype == idaapi.NN_call:
            target = insn.ops[0]
            if target.type == idaapi.o_near:
                target_ea = target.addr
                target_name = idc.get_func_name(target_ea)
                if target_name:
                    calls.append({
                        'address': hex(ea),
                        'target': hex(target_ea),
                        'function': target_name
                    })
                    print(f"  {ea:#08x} -> {target_name}")
        
        ea = idc.next_head(ea, func.end_ea)
    
    results['farobj_step_terrain_clamp'] = {
        'address': hex(func_ea),
        'size': func.end_ea - func.start_ea,
        'calls': calls,
        'disassembly': disasm_lines
    }
    
    print(f"\nTotal calls: {len(calls)}")
    
    # Check what calls this function
    print("\nCallers of farobj_step_terrain_clamp:")
    caller_count = 0
    for xref in idautils.XrefsTo(func_ea):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(xref.frm)
                print(f"  {xref.frm:#08x} in {caller_name}")
                caller_count += 1
    print(f"Total callers: {caller_count}")

# Function 3: ai_entity_update_step @ 0x3D37F (LARGE - 1319 bytes)
print(f"\n{'=' * 80}")
print("ANALYZING: ai_entity_update_step @ 0x3D37F (1319 bytes)")
print("=" * 80)

func_ea = 0x3D37F
func = idaapi.get_func(func_ea)

if func:
    func_name = idc.get_func_name(func_ea)
    print(f"Function: {func_name}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    print("(Large function - analyzing structure)\n")
    
    # Get first 50 instructions to understand structure
    print("First 50 instructions:")
    ea = func.start_ea
    count = 0
    disasm_lines = []
    
    while ea < func.end_ea and count < 50:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({
            'address': hex(ea),
            'disasm': disasm
        })
        print(f"  {ea:#08x}: {disasm}")
        ea = idc.next_head(ea, func.end_ea)
        count += 1
    
    print(f"\n... (showing first 50 of ~{(func.end_ea - func.start_ea) // 3} instructions)")
    
    # Find all function calls
    print("\nFunction calls made (this reveals what it does):")
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        insn = idaapi.insn_t()
        insn_len = idaapi.decode_insn(insn, ea)
        
        if insn_len > 0 and insn.itype == idaapi.NN_call:
            target = insn.ops[0]
            if target.type == idaapi.o_near:
                target_ea = target.addr
                target_name = idc.get_func_name(target_ea)
                if target_name:
                    calls.append({
                        'address': hex(ea),
                        'target': hex(target_ea),
                        'function': target_name
                    })
                    print(f"  {ea:#08x} -> {target_name}")
        
        ea = idc.next_head(ea, func.end_ea)
    
    results['ai_entity_update_step'] = {
        'address': hex(func_ea),
        'size': func.end_ea - func.start_ea,
        'calls': calls,
        'disassembly_sample': disasm_lines
    }
    
    print(f"\nTotal function calls: {len(calls)}")
    
    # Check what calls this function
    print("\nCallers of ai_entity_update_step:")
    caller_count = 0
    for xref in idautils.XrefsTo(func_ea):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(xref.frm)
                print(f"  {xref.frm:#08x} in {caller_name}")
                caller_count += 1
    print(f"Total callers: {caller_count}")

# Save results
output_file = Path(__file__).parent / "entity_update_analysis.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_file}")
print("Exiting IDA...")

# Exit
idc.qexit(0)
