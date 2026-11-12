"""
Extract actual CALL instructions from view_projection.
This corrects the false "math helpers" finding.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def analyze_function_calls(func_addr, func_name):
    """Extract all CALL instructions from a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        print(f"✗ No function at {hex(func_addr)}")
        return None
    
    print(f"\nAnalyzing {func_name} at {hex(func_addr)}")
    print(f"  Range: {hex(func.start_ea)} - {hex(func.end_ea)}")
    print(f"  Size: {func.end_ea - func.start_ea} bytes")
    
    calls = []
    ea = func.start_ea
    
    while ea < func.end_ea:
        # Get instruction mnemonic
        mnem = idc.print_insn_mnem(ea)
        
        # Check if it's a CALL instruction
        if mnem and mnem.startswith("call"):
            # Get operand (target address)
            op_type = idc.get_operand_type(ea, 0)
            
            if op_type == idc.o_near or op_type == idc.o_far:
                # Direct call to address
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_func_name(target)
                
                if not target_name:
                    target_name = idc.get_name(target)
                if not target_name:
                    target_name = f"sub_{target:X}"
                
                call_info = {
                    "call_ea": hex(ea),
                    "target_ea": hex(target),
                    "target_name": target_name,
                    "call_type": "direct",
                    "disasm": idc.GetDisasm(ea)
                }
                calls.append(call_info)
                print(f"    {hex(ea)}: call {target_name} ({hex(target)})")
                
            elif op_type == idc.o_reg:
                # Indirect call via register
                reg_name = idc.print_operand(ea, 0)
                call_info = {
                    "call_ea": hex(ea),
                    "target_ea": None,
                    "target_name": f"indirect via {reg_name}",
                    "call_type": "indirect_reg",
                    "disasm": idc.GetDisasm(ea)
                }
                calls.append(call_info)
                print(f"    {hex(ea)}: call {reg_name} (indirect)")
                
            elif op_type == idc.o_mem or op_type == idc.o_displ:
                # Indirect call via memory
                mem_desc = idc.print_operand(ea, 0)
                call_info = {
                    "call_ea": hex(ea),
                    "target_ea": None,
                    "target_name": f"indirect via [{mem_desc}]",
                    "call_type": "indirect_mem",
                    "disasm": idc.GetDisasm(ea)
                }
                calls.append(call_info)
                print(f"    {hex(ea)}: call [{mem_desc}] (indirect)")
        
        # Move to next instruction
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"\n  Total CALL instructions: {len(calls)}")
    return calls

def categorize_calls(calls):
    """Categorize calls by type."""
    direct_calls = [c for c in calls if c["call_type"] == "direct"]
    indirect_calls = [c for c in calls if c["call_type"].startswith("indirect")]
    
    print(f"\n  Direct calls: {len(direct_calls)}")
    print(f"  Indirect calls: {len(indirect_calls)}")
    
    # Count calls to each target
    call_counts = {}
    for call in direct_calls:
        target = call["target_name"]
        if target not in call_counts:
            call_counts[target] = 0
        call_counts[target] += 1
    
    print(f"\n  Unique direct targets: {len(call_counts)}")
    print("\n  Call frequency:")
    for target, count in sorted(call_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {target}: {count}x")
    
    return {
        "direct": direct_calls,
        "indirect": indirect_calls,
        "call_counts": call_counts
    }

def main():
    """Analyze view_projection and other key functions."""
    print("="*80)
    print("EXTRACTING ACTUAL CALL INSTRUCTIONS")
    print("="*80)
    
    # Analyze view_projection
    view_proj_addr = idc.get_name_ea_simple("view_projection")
    if view_proj_addr == idc.BADADDR:
        view_proj_addr = 0x20BDB
    
    view_proj_calls = analyze_function_calls(view_proj_addr, "view_projection")
    
    if view_proj_calls:
        view_proj_analysis = categorize_calls(view_proj_calls)
    else:
        view_proj_analysis = None
    
    # Also analyze record_xform_apply (has 4x vec3 calls)
    print("\n" + "="*80)
    record_xform_addr = idc.get_name_ea_simple("record_xform_apply")
    record_xform_calls = None
    record_xform_analysis = None
    
    if record_xform_addr != idc.BADADDR:
        record_xform_calls = analyze_function_calls(record_xform_addr, "record_xform_apply")
        if record_xform_calls:
            record_xform_analysis = categorize_calls(record_xform_calls)
    
    # Save results
    results = {
        "view_projection": {
            "address": hex(view_proj_addr),
            "total_calls": len(view_proj_calls) if view_proj_calls else 0,
            "calls": view_proj_calls,
            "analysis": view_proj_analysis
        }
    }
    
    if record_xform_calls:
        results["record_xform_apply"] = {
            "address": hex(record_xform_addr),
            "total_calls": len(record_xform_calls),
            "calls": record_xform_calls,
            "analysis": record_xform_analysis
        }
    
    output_file = Path(__file__).parent / "actual_call_targets.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print(f"Results saved to: {output_file}")
    print("="*80)
    
    # Exit IDA
    idc.qexit(0)

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
