"""
Verify farobj system - 4 functions, 2 queues, complete call graph.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

def analyze_farobj_function(func_name):
    """Analyze a farobj function."""
    addr = idc.get_name_ea_simple(func_name)
    if addr == idc.BADADDR:
        return None
    
    func = idaapi.get_func(addr)
    if not func:
        return None
    
    # Get calls
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
                    "from": hex(ea),
                    "to": hex(target),
                    "name": target_name
                })
        ea = idc.next_head(ea, func.end_ea)
    
    # Get callers
    xrefs = list(idautils.XrefsTo(func.start_ea, 0))
    callers = {}
    for xref in xrefs:
        caller_name = idc.get_func_name(xref.frm)
        if caller_name:
            callers[caller_name] = callers.get(caller_name, 0) + 1
    
    # Check for queue references
    queue_refs = []
    ea = func.start_ea
    while ea < func.end_ea:
        for i in range(2):
            op_type = idc.get_operand_type(ea, i)
            if op_type in (idc.o_mem, idc.o_displ):
                op_val = idc.get_operand_value(ea, i)
                name = idc.get_name(op_val)
                if name and ("7c054" in name.lower() or "7d0c6" in name.lower() or "queue" in name.lower()):
                    queue_refs.append({
                        "address": hex(ea),
                        "target": hex(op_val),
                        "name": name,
                        "disasm": idc.GetDisasm(ea)
                    })
        ea = idc.next_head(ea, func.end_ea)
    
    return {
        "name": func_name,
        "address": hex(addr),
        "size": func.end_ea - func.start_ea,
        "calls": calls,
        "call_count": len(calls),
        "callers": callers,
        "caller_count": len(callers),
        "queue_refs": queue_refs
    }

def main():
    print("="*80)
    print("FAROBJ SYSTEM VERIFICATION")
    print("="*80)
    
    farobj_functions = [
        "farobj_record_step",
        "farobj_record_push_7c054",
        "farobj_record_lookup_step",
        "farobj_record_push_7d0c6"
    ]
    
    results = {}
    
    for func_name in farobj_functions:
        print(f"\n--- {func_name} ---")
        analysis = analyze_farobj_function(func_name)
        
        if analysis:
            print(f"Address: {analysis['address']}")
            print(f"Size: {analysis['size']} bytes")
            print(f"Calls: {analysis['call_count']}")
            print(f"Called by: {analysis['caller_count']} functions")
            for caller, count in sorted(analysis['callers'].items()):
                print(f"  - {caller} ({count}x)")
            
            if analysis['queue_refs']:
                print(f"Queue references: {len(analysis['queue_refs'])}")
                for ref in analysis['queue_refs']:
                    print(f"  - {ref['disasm']}")
            
            results[func_name] = analysis
        else:
            print(f"✗ Not found")
            results[func_name] = {"error": "not_found"}
    
    # Check farobj_sort_and_step
    print(f"\n--- farobj_sort_and_step (orchestrator) ---")
    sort_addr = idc.get_name_ea_simple("farobj_sort_and_step")
    if sort_addr != idc.BADADDR:
        sort_analysis = analyze_farobj_function("farobj_sort_and_step")
        if sort_analysis:
            print(f"Address: {sort_analysis['address']}")
            print(f"Size: {sort_analysis['size']} bytes")
            print(f"Calls to farobj functions:")
            for call in sort_analysis['calls']:
                if "farobj" in call['name']:
                    print(f"  - {call['name']}")
            results["farobj_sort_and_step"] = sort_analysis
    
    # Verify queues
    print(f"\n{'='*80}")
    print("QUEUE VERIFICATION")
    print("="*80)
    
    dgroup_base = idc.get_segm_by_sel(idc.selector_by_name("DGROUP"))
    if dgroup_base != idc.BADADDR:
        near_queue = dgroup_base + 0x7C054
        far_queue = dgroup_base + 0x7D0C6
        
        near_name = idc.get_name(near_queue)
        far_name = idc.get_name(far_queue)
        
        print(f"Near queue (DGROUP:0x7C054):")
        print(f"  Address: {hex(near_queue)}")
        print(f"  Name: {near_name}")
        
        print(f"\nFar queue (DGROUP:0x7D0C6):")
        print(f"  Address: {hex(far_queue)}")
        print(f"  Name: {far_name}")
        
        separation = far_queue - near_queue
        print(f"\nQueue separation: {separation} bytes (0x{separation:X})")
        
        if separation == 4210:
            print("✓ Matches expected 4,210 bytes")
        else:
            print(f"⚠ Expected 4,210, got {separation}")
        
        results["queues"] = {
            "near": {"address": hex(near_queue), "name": near_name},
            "far": {"address": hex(far_queue), "name": far_name},
            "separation": separation
        }
    
    # Save
    output_file = Path(__file__).parent / "farobj_verification.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"Results saved to: {output_file}")
    print("="*80)
    
    idc.qexit(0)

if __name__ == "__main__":
    idaapi.auto_wait()
    main()
