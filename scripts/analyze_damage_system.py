"""
Analyze weapon damage system.

Key functions:
- damage_event_dispatch_handler @ 0x2EAA7 (190 bytes)
- store_impact_step @ 0x397FB (169 bytes)
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

print("=" * 80)
print("WEAPON DAMAGE SYSTEM ANALYSIS")
print("=" * 80)

# Wait for auto-analysis
print("Waiting for auto-analysis...")
idaapi.auto_wait()
print("Auto-analysis complete\n")

results = {
    'damage_event_dispatch_handler': {},
    'store_impact_step': {},
    'related_functions': []
}

# Analyze damage_event_dispatch_handler
func_ea = 0x2EAA7
func = idaapi.get_func(func_ea)

if func:
    print(f"Analyzing damage_event_dispatch_handler @ {func_ea:#x}")
    print(f"Size: {func.end_ea - func.start_ea} bytes\n")
    
    # Get disassembly
    disasm_lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({
            'address': hex(ea),
            'disasm': disasm
        })
        ea = idc.next_head(ea, func.end_ea)
    
    results['damage_event_dispatch_handler'] = {
        'address': hex(func_ea),
        'size': func.end_ea - func.start_ea,
        'disassembly': disasm_lines
    }
    
    print(f"Extracted {len(disasm_lines)} instructions")
    
    # Look for function calls
    print("\nCalls from damage_event_dispatch_handler:")
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
                    print(f"  {ea:#x} -> {target_name} @ {target_ea:#x}")
        
        ea = idc.next_head(ea, func.end_ea)

# Analyze store_impact_step
print(f"\n{'=' * 80}")
func_ea = 0x397FB
func = idaapi.get_func(func_ea)

if func:
    print(f"Analyzing store_impact_step @ {func_ea:#x}")
    print(f"Size: {func.end_ea - func.start_ea} bytes\n")
    
    # Get disassembly
    disasm_lines = []
    ea = func.start_ea
    while ea < func.end_ea:
        disasm = idc.generate_disasm_line(ea, 0)
        disasm_lines.append({
            'address': hex(ea),
            'disasm': disasm
        })
        ea = idc.next_head(ea, func.end_ea)
    
    results['store_impact_step'] = {
        'address': hex(func_ea),
        'size': func.end_ea - func.start_ea,
        'disassembly': disasm_lines
    }
    
    print(f"Extracted {len(disasm_lines)} instructions")
    
    # Look for function calls
    print("\nCalls from store_impact_step:")
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
                    print(f"  {ea:#x} -> {target_name} @ {target_ea:#x}")
        
        ea = idc.next_head(ea, func.end_ea)

# Find what calls these functions (reverse lookup)
print(f"\n{'=' * 80}")
print("Finding callers of damage functions...")

for func_name, func_addr in [('damage_event_dispatch_handler', 0x2EAA7), ('store_impact_step', 0x397FB)]:
    print(f"\nCallers of {func_name}:")
    caller_count = 0
    
    for xref in idautils.XrefsTo(func_addr):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:  # Call near/far
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(xref.frm)
                print(f"  {xref.frm:#x} in {caller_name}")
                caller_count += 1
                
                if caller_count <= 10:  # Store first 10
                    results['related_functions'].append({
                        'caller': caller_name,
                        'caller_addr': hex(xref.frm),
                        'callee': func_name,
                        'callee_addr': hex(func_addr)
                    })
    
    if caller_count == 0:
        print("  (No callers found)")

# Save results
output_file = Path(__file__).parent / "damage_system_analysis.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'=' * 80}")
print(f"Results saved to: {output_file}")
print("Exiting IDA...")

# Exit
idc.qexit(0)
