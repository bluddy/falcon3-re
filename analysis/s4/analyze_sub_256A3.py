"""
Analyze sub_256A3 - unknown function called from main game loop.
Position 10/44 in game_frame_pipeline_step, between terrain and entity processing.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def analyze_function_complete(addr, name):
    """Complete analysis of a function."""
    
    func = idaapi.get_func(addr)
    if not func:
        return None
    
    print("="*80)
    print(f"ANALYZING: {name}")
    print("="*80)
    print(f"Address: {hex(addr)}")
    print(f"Segment:Offset: {idc.get_segm_name(addr)}:{hex(addr - idc.get_segm_start(addr))}")
    print(f"Size: {func.end_ea - func.start_ea} bytes")
    
    # Get all CALL instructions
    calls = []
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
                print(f"  {hex(ea)}: call {target_name}")
        ea = idc.next_head(ea, func.end_ea)
    
    print(f"\nTotal calls: {len(calls)}")
    
    # Get callers
    xrefs = list(idautils.XrefsTo(func.start_ea, 0))
    callers = {}
    for xref in xrefs:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            callers[caller_name] = callers.get(caller_name, 0) + 1
    
    print(f"\nCalled by {len(callers)} functions ({len(xrefs)} call sites):")
    for caller, count in sorted(callers.items()):
        print(f"  - {caller} ({count}x)")
    
    # Look for DGROUP references
    print(f"\n{'='*80}")
    print("DATA REFERENCES")
    print("="*80)
    
    dgroup_refs = []
    ea = func.start_ea
    while ea < func.end_ea:
        # Check all operands
        for i in range(idc.get_operand_count(ea)):
            op_type = idc.get_operand_type(ea, i)
            if op_type in (idc.o_mem, idc.o_displ):
                op_val = idc.get_operand_value(ea, i)
                name = idc.get_name(op_val)
                
                # Check if it's in DGROUP
                seg_name = idc.get_segm_name(op_val)
                if seg_name == "DGROUP" or (name and "dgroup" in name.lower()):
                    dgroup_refs.append({
                        "address": hex(ea),
                        "data_addr": hex(op_val),
                        "name": name if name else "unnamed",
                        "disasm": idc.GetDisasm(ea)
                    })
                    
                    # Check if this is DGROUP:0x4287
                    dgroup_base = idc.get_segm_start(idc.get_segm_by_name("DGROUP"))
                    if dgroup_base != idc.BADADDR:
                        offset = op_val - dgroup_base
                        if offset == 0x4287:
                            print(f"⭐ FOUND DGROUP:0x4287 reference!")
                            print(f"  at {hex(ea)}: {idc.GetDisasm(ea)}")
        
        ea = idc.next_head(ea, func.end_ea)
    
    if dgroup_refs:
        print(f"\nFound {len(dgroup_refs)} DGROUP references:")
        for ref in dgroup_refs:
            print(f"  {ref['address']}: {ref['disasm']}")
            print(f"    → {ref['name']} at {ref['data_addr']}")
    else:
        print("\nNo DGROUP references found")
    
    # Check for view_projection calls
    print(f"\n{'='*80}")
    print("VIEW/PROJECTION CONNECTIONS")
    print("="*80)
    
    view_related = [c for c in calls if any(kw in c['name'].lower() 
                    for kw in ['view', 'proj', 'transform', 'camera', 'matrix'])]
    
    if view_related:
        print(f"Found {len(view_related)} view/projection related calls:")
        for call in view_related:
            print(f"  - {call['name']}")
    else:
        print("No obvious view/projection calls found")
    
    # Check for rendering-related calls
    rendering_related = [c for c in calls if any(kw in c['name'].lower() 
                        for kw in ['render', 'draw', 'display', 'graphics', 'farobj'])]
    
    if rendering_related:
        print(f"\nFound {len(rendering_related)} rendering-related calls:")
        for call in rendering_related:
            print(f"  - {call['name']}")
    
    return {
        "name": name,
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "calls": calls,
        "call_count": len(calls),
        "callers": callers,
        "dgroup_refs": dgroup_refs,
        "view_related_calls": view_related,
        "rendering_related_calls": rendering_related
    }

def check_dgroup_4287():
    """Specifically investigate DGROUP:0x4287."""
    
    print("\n" + "="*80)
    print("INVESTIGATING DGROUP:0x4287")
    print("="*80)
    
    dgroup_base = idc.get_segm_start(idc.get_segm_by_name("DGROUP"))
    if dgroup_base == idc.BADADDR:
        print("✗ DGROUP segment not found")
        return None
    
    target_addr = dgroup_base + 0x4287
    print(f"Linear address: {hex(target_addr)}")
    
    # Get name and type
    name = idc.get_name(target_addr)
    type_str = idc.get_type(target_addr)
    
    print(f"Name: {name if name else 'unnamed'}")
    print(f"Type: {type_str if type_str else 'unknown'}")
    
    # Get xrefs to this data
    xrefs = list(idautils.XrefsTo(target_addr, 0))
    print(f"\nReferenced by {len(xrefs)} locations:")
    
    xref_funcs = {}
    for xref in xrefs:
        func_name = idc.get_func_name(xref.frm)
        if func_name:
            if func_name not in xref_funcs:
                xref_funcs[func_name] = []
            xref_funcs[func_name].append({
                "address": hex(xref.frm),
                "disasm": idc.GetDisasm(xref.frm)
            })
    
    for func_name, refs in sorted(xref_funcs.items()):
        print(f"\n  {func_name} ({len(refs)} refs):")
        for ref in refs[:3]:  # First 3
            print(f"    {ref['address']}: {ref['disasm']}")
    
    # Try to determine structure size by looking at nearby accesses
    print(f"\n{'='*80}")
    print("STRUCTURE SIZE ESTIMATION")
    print("="*80)
    
    max_offset = 0
    for xref in xrefs:
        disasm = idc.GetDisasm(xref.frm)
        # Look for offset patterns like [DGROUP:4287+8]
        if '+' in disasm:
            try:
                # Try to extract offset
                parts = disasm.split('+')
                for part in parts:
                    if 'h' in part or any(c.isdigit() for c in part):
                        # Rough offset extraction
                        pass
            except:
                pass
    
    return {
        "address": hex(target_addr),
        "name": name,
        "type": type_str,
        "xref_count": len(xrefs),
        "used_by": list(xref_funcs.keys())
    }

def main():
    print("="*80)
    print("sub_256A3 ANALYSIS")
    print("Called from game_frame_pipeline_step at position 10/44")
    print("="*80)
    
    # Analyze sub_256A3
    addr = idc.get_name_ea_simple("sub_256A3")
    if addr == idc.BADADDR:
        addr = 0x256A3
    
    analysis = analyze_function_complete(addr, "sub_256A3")
    
    # Check DGROUP:0x4287
    dgroup_analysis = check_dgroup_4287()
    
    # Save results
    results = {
        "sub_256A3": analysis,
        "dgroup_4287": dgroup_analysis
    }
    
    output_file = Path(__file__).parent / "sub_256A3_analysis.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*80)
    print(f"Results saved to: {output_file}")
    print("="*80)
    
    # Suggest a name based on findings
    print("\n" + "="*80)
    print("NAME SUGGESTION")
    print("="*80)
    
    if analysis:
        if dgroup_analysis and dgroup_analysis['used_by']:
            print("Based on DGROUP:0x4287 usage and position in game loop:")
            print("Possible names:")
            print("  - view_state_update")
            print("  - camera_position_sync")
            print("  - coord_transform_prepare")
            print("  - view_matrix_setup")
        
        if analysis['view_related_calls']:
            print("\nHas view/projection calls - likely view setup function")
    
    idc.qexit(0)

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
