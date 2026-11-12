"""
Analyze game_frame_pipeline_step - the main game loop.
This is a critical discovery from farobj analysis.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def analyze_game_loop():
    """Deep dive into the main game loop."""
    
    func_name = "game_frame_pipeline_step"
    addr = idc.get_name_ea_simple(func_name)
    
    if addr == idc.BADADDR:
        print(f"✗ {func_name} not found")
        return None
    
    func = idaapi.get_func(addr)
    if not func:
        print(f"✗ No function at {hex(addr)}")
        return None
    
    print("="*80)
    print("GAME LOOP ANALYSIS: game_frame_pipeline_step")
    print("="*80)
    print(f"Address: {hex(addr)}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    
    # Extract all CALL instructions
    calls = []
    call_counts = {}
    ea = func.start_ea
    
    while ea < func.end_ea:
        mnem = idc.print_insn_mnem(ea)
        if mnem and mnem.startswith("call"):
            op_type = idc.get_operand_type(ea, 0)
            if op_type in (idc.o_near, idc.o_far):
                target = idc.get_operand_value(ea, 0)
                target_name = idc.get_func_name(target) or idc.get_name(target) or f"sub_{target:X}"
                
                calls.append({
                    "address": hex(ea),
                    "target": hex(target),
                    "name": target_name,
                    "disasm": idc.GetDisasm(ea)
                })
                
                call_counts[target_name] = call_counts.get(target_name, 0) + 1
        
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"\nTotal CALL instructions: {len(calls)}")
    print(f"Unique functions called: {len(call_counts)}")
    
    # Show calls in order
    print(f"\n{'='*80}")
    print("CALL SEQUENCE (execution order):")
    print("="*80)
    
    for i, call in enumerate(calls, 1):
        print(f"{i:3}. {call['address']}: {call['name']}")
    
    # Show call frequency
    print(f"\n{'='*80}")
    print("CALL FREQUENCY:")
    print("="*80)
    
    sorted_calls = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_calls:
        marker = " ⭐" if count >= 3 else ""
        print(f"  {name}: {count}x{marker}")
    
    # Identify rendering-related calls
    print(f"\n{'='*80}")
    print("RENDERING SUBSYSTEMS:")
    print("="*80)
    
    rendering_keywords = ["farobj", "view", "proj", "render", "draw", "display", "graphics"]
    rendering_calls = [c for c in calls if any(kw in c['name'].lower() for kw in rendering_keywords)]
    
    print(f"Found {len(rendering_calls)} rendering-related calls:")
    for call in rendering_calls:
        print(f"  - {call['name']} at {call['address']}")
    
    # Get callers
    xrefs = list(idautils.XrefsTo(func.start_ea, 0))
    callers = {}
    for xref in xrefs:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            callers[caller_name] = callers.get(caller_name, 0) + 1
    
    print(f"\n{'='*80}")
    print(f"CALLED BY ({len(callers)} functions, {len(xrefs)} call sites):")
    print("="*80)
    
    for caller, count in sorted(callers.items()):
        print(f"  - {caller} ({count}x)")
    
    return {
        "name": func_name,
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "total_calls": len(calls),
        "unique_targets": len(call_counts),
        "calls": calls,
        "call_frequency": call_counts,
        "rendering_calls": rendering_calls,
        "callers": callers
    }

def main():
    result = analyze_game_loop()
    
    if result:
        output_file = Path(__file__).parent / "game_loop_analysis.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"\n{'='*80}")
        print(f"Results saved to: {output_file}")
        print("="*80)
    
    idc.qexit(0)

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
