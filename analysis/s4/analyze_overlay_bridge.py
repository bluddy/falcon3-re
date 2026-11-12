"""
Analyze overlay_tail_bridge (0x166F) - newly discovered function.
This is called by view_projection and may trigger overlay swaps.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def analyze_function_detailed(func_addr, func_name):
    """Deep analysis of a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    print(f"\n{'='*80}")
    print(f"ANALYZING: {func_name}")
    print(f"{'='*80}")
    print(f"Address: {hex(func_addr)}")
    print(f"Range: {hex(func.start_ea)} - {hex(func.end_ea)}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    
    # Get all calls
    calls = []
    ea = func.start_ea
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        if mnem and mnem.startswith("call"):
            op_type = idc.get_operand_type(ea, 0)
            if op_type == idc.o_near or op_type == idc.o_far:
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_func_name(target) or idc.get_name(target) or f"sub_{target:X}"
                calls.append({
                    "address": hex(ea),
                    "target": hex(target),
                    "name": target_name,
                    "disasm": idc.GetDisasm(ea)
                })
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"\nCALL instructions: {len(calls)}")
    for call in calls:
        print(f"  {call['address']}: {call['disasm']}")
    
    # Get callers
    xrefs = list(idautils.XrefsTo(func.start_ea, 0))
    callers = {}
    for xref in xrefs:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            if caller_name not in callers:
                callers[caller_name] = []
            callers[caller_name].append(hex(xref.frm))
    
    print(f"\nCalled by {len(callers)} functions ({len(xrefs)} call sites):")
    for caller, sites in sorted(callers.items()):
        print(f"  {caller}: {len(sites)}x")
        for site in sites[:3]:
            print(f"    from {site}")
    
    # Check for overlay-related patterns
    print(f"\nChecking for overlay patterns...")
    
    # Look for references to overlay tables or segments
    ea = func.start_ea
    overlay_refs = []
    while ea < func.end_ea:
        for i in range(idc.get_operand_count(ea)):
            op_type = idc.get_operand_type(ea, i)
            if op_type == idc.o_mem or op_type == idc.o_imm:
                op_val = idc.get_operand_value(ea, i)
                # Check if it references data segment
                name = idc.get_name(op_val)
                if name and ("overlay" in name.lower() or "swap" in name.lower() or "segment" in name.lower()):
                    overlay_refs.append({
                        "address": hex(ea),
                        "operand": i,
                        "value": hex(op_val),
                        "name": name,
                        "disasm": idc.GetDisasm(ea)
                    })
        ea = idc.next_head(ea, func.end_ea)
    
    if overlay_refs:
        print(f"\nFound {len(overlay_refs)} overlay-related references:")
        for ref in overlay_refs:
            print(f"  {ref['address']}: {ref['disasm']}")
            print(f"    → {ref['name']} at {ref['value']}")
    else:
        print("  No obvious overlay references found in operands")
    
    return {
        "name": func_name,
        "address": hex(func_addr),
        "size": func.end_ea - func.start_ea,
        "calls": calls,
        "callers": {k: v for k, v in callers.items()},
        "overlay_refs": overlay_refs
    }

def main():
    print("="*80)
    print("OVERLAY_TAIL_BRIDGE ANALYSIS")
    print("="*80)
    
    # Find overlay_tail_bridge
    bridge_addr = idc.get_name_ea_simple("overlay_tail_bridge")
    if bridge_addr == idc.BADADDR:
        bridge_addr = 0x166F
    
    bridge_analysis = analyze_function_detailed(bridge_addr, "overlay_tail_bridge")
    
    # Also analyze its callees
    print(f"\n{'='*80}")
    print("ANALYZING CALLEES")
    print("="*80)
    
    callees = {}
    if bridge_analysis and bridge_analysis["calls"]:
        for call in bridge_analysis["calls"][:5]:  # First 5
            callee_addr = int(call["target"], 16)
            callee_name = call["name"]
            
            print(f"\n--- {callee_name} ---")
            callee_func = idaapi.get_func(callee_addr)
            if callee_func:
                print(f"Address: {call['target']}")
                print(f"Size: {callee_func.end_ea - callee_func.start_ea} bytes")
                
                # Check if it's in overlay segment
                seg = idaapi.getseg(callee_addr)
                if seg:
                    seg_name = idaapi.get_segm_name(seg)
                    print(f"Segment: {seg_name}")
                    
                    if seg_name and seg_name.startswith("R"):
                        print(f"  → OVERLAY SEGMENT!")
                        callees[callee_name] = {
                            "address": call['target'],
                            "segment": seg_name,
                            "is_overlay": True
                        }
                    else:
                        callees[callee_name] = {
                            "address": call['target'],
                            "segment": seg_name,
                            "is_overlay": False
                        }
    
    # Save results
    results = {
        "overlay_tail_bridge": bridge_analysis,
        "callees": callees,
        "analysis_notes": {
            "purpose": "Bridge function for overlay management",
            "called_from_view_projection": True,
            "may_trigger_swaps": len(callees) > 0
        }
    }
    
    output_file = Path(__file__).parent / "overlay_bridge_analysis.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Results saved to: {output_file}")
    print("="*80)
    
    # Exit IDA
    idc.qexit(0)

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
