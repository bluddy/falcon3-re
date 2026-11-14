"""
Analyze the final 9 remaining AI functions in detail.

This is a focused analysis to complete the AI system function naming.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

# Final 9 remaining AI functions
TARGET_FUNCTIONS = [
    (0x40D26, "sub_40D26", 81),
    (0x3DED9, "sub_3DED9", 69),
    (0x42838, "sub_42838", 64),
    (0x3F788, "sub_3F788", 25),
    (0x408E7, "sub_408E7", 24),
    (0x3F700, "sub_3F700", 24),
    (0x49982, "sub_49982", 21),
    (0x3F5B4, "sub_3F5B4", 19),
    (0x40C6A, "sub_40C6A", 9),
]

def get_callees(func_addr):
    """Get all functions called."""
    callees = []
    func = idaapi.get_func(func_addr)
    if not func:
        return callees
    
    seen = set()
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                target_func = idaapi.get_func(xref.to)
                if target_func and target_func.start_ea not in seen:
                    seen.add(target_func.start_ea)
                    callees.append({
                        'address': target_func.start_ea,
                        'name': idc.get_func_name(target_func.start_ea)
                    })
    return callees

def get_callers(func_addr):
    """Get functions that call this function."""
    callers = []
    seen = set()
    for xref in idautils.XrefsTo(func_addr, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func and caller_func.start_ea not in seen:
                seen.add(caller_func.start_ea)
                callers.append({
                    'address': caller_func.start_ea,
                    'name': idc.get_func_name(caller_func.start_ea)
                })
    return callers

def get_first_n_instructions(func_addr, n=20):
    """Get first N instructions."""
    func = idaapi.get_func(func_addr)
    if not func:
        return []
    
    instructions = []
    count = 0
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if count >= n:
            break
        instructions.append({
            'address': head,
            'offset': head - func.start_ea,
            'mnem': idc.print_insn_mnem(head),
            'disasm': idc.generate_disasm_line(head, 0)
        })
        count += 1
    return instructions

def analyze_function(addr, name, size):
    """Analyze a function in detail."""
    print(f"\n{'='*80}")
    print(f"{name} @ {addr:#08x} ({size}B)")
    print(f"{'='*80}")
    
    func = idaapi.get_func(addr)
    if not func:
        print("ERROR: Not a function!")
        return None
    
    callees = get_callees(addr)
    callers = get_callers(addr)
    instructions = get_first_n_instructions(addr, 20)
    
    # Analyze patterns
    cmp_count = sum(1 for i in instructions if i['mnem'] in ['cmp', 'test'])
    has_si_di = any('si' in i['disasm'].lower() or 'di' in i['disasm'].lower() for i in instructions)
    has_loop = any('loop' in i['mnem'] for i in instructions)
    
    print(f"\nCallees ({len(callees)}):")
    for c in callees:
        print(f"  -> {c['name']}")
    
    print(f"\nCallers ({len(callers)}):")
    for c in callers[:10]:
        print(f"  <- {c['name']}")
    
    print(f"\nPatterns:")
    print(f"  Comparisons: {cmp_count}")
    print(f"  SI/DI access: {has_si_di}")
    print(f"  Has loop: {has_loop}")
    print(f"  Is leaf: {len(callees) == 0}")
    
    print(f"\nFirst 15 instructions:")
    for i in instructions[:15]:
        print(f"  +{i['offset']:04x}: {i['disasm']}")
    
    # Suggest name based on analysis
    suggested = "ai_unknown"
    confidence = "low"
    reasoning = []
    
    # Check callees for hints
    if callees:
        for callee in callees:
            cname = callee['name'].lower()
            if 'angle' in cname or 'heading' in cname:
                suggested = "ai_angle_helper"
                confidence = "medium"
                reasoning.append(f"Calls {callee['name']}")
            elif 'vector' in cname or 'vec3' in cname:
                suggested = "ai_vector_helper"
                confidence = "medium"
                reasoning.append(f"Calls {callee['name']}")
            elif 'flag' in cname or 'gate' in cname:
                suggested = "ai_flag_check"
                confidence = "medium"
                reasoning.append(f"Calls {callee['name']}")
    
    # Check if it's a leaf with comparisons
    if len(callees) == 0 and cmp_count > 3:
        suggested = "ai_state_dispatcher"
        confidence = "medium"
        reasoning.append(f"Leaf with {cmp_count} comparisons")
    elif len(callees) == 0:
        suggested = "ai_field_accessor"
        confidence = "low"
        reasoning.append("Leaf function (pure calculation)")
    
    # Check caller patterns
    ai_callers = [c for c in callers if 'ai_' in c['name']]
    if len(ai_callers) > 5:
        confidence = "medium"
        reasoning.append(f"Widely used by AI ({len(ai_callers)} callers)")
    
    print(f"\nSuggested: {suggested} [{confidence}]")
    if reasoning:
        print(f"Reasoning:")
        for r in reasoning:
            print(f"  - {r}")
    
    return {
        'address': addr,
        'name': name,
        'size': size,
        'callees': callees,
        'callers': callers,
        'instructions': instructions[:15],
        'cmp_count': cmp_count,
        'has_si_di': has_si_di,
        'has_loop': has_loop,
        'is_leaf': len(callees) == 0,
        'suggested_name': suggested,
        'confidence': confidence,
        'reasoning': reasoning
    }

def main():
    print("="*80)
    print("ANALYZING FINAL 9 AI FUNCTIONS")
    print("="*80)
    
    idaapi.auto_wait()
    
    results = []
    for addr, name, size in TARGET_FUNCTIONS:
        result = analyze_function(addr, name, size)
        if result:
            results.append(result)
    
    # Save results
    output_path = Path(__file__).parent.parent / "ai_final_9_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Analysis saved to: {output_path}")
    print(f"{'='*80}")
    
    # Summary
    print(f"\nSummary:")
    for r in results:
        print(f"  {r['name']:20} -> {r['suggested_name']:30} [{r['confidence']}]")
    
    idc.qexit(0)

if __name__ == "__main__":
    main()
