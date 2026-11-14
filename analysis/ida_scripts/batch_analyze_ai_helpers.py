"""
Batch analyze remaining AI helper functions to identify patterns and name them.

This script analyzes the 55 remaining AI functions by looking at:
- What they call (callees)
- What calls them (callers)
- Key data accesses
- Instruction patterns

Strategy: Group by similarity and assign names based on patterns.
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

# Remaining functions to analyze (from ai_callees_report, minus the 10 we already named)
ALREADY_NAMED = [0x3CF9D, 0x3D37F, 0x3F3A8, 0x49997, 0x407C0, 0x423A9, 0x40884, 0x3EB4E, 0x425A2, 0x42503]

def get_function_signature(func_addr):
    """Get a signature of function characteristics for pattern matching."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    size = func.end_ea - func.start_ea
    
    # Get callees
    callees = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                target_func = idaapi.get_func(xref.to)
                if target_func:
                    callees.append(idc.get_func_name(target_func.start_ea))
    
    callees = list(set(callees))  # Dedupe
    
    # Get callers
    callers = []
    for xref in idautils.XrefsTo(func_addr, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                callers.append(idc.get_func_name(caller_func.start_ea))
    
    callers = list(set(callers))
    
    # Analyze instructions
    has_loop = False
    has_far_call = False
    cmp_count = 0
    has_si_di = False
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head)
        disasm = idc.generate_disasm_line(head, 0)
        
        if mnem in ['loop', 'loope', 'loopne']:
            has_loop = True
        if 'far ptr' in disasm:
            has_far_call = True
        if mnem in ['cmp', 'test']:
            cmp_count += 1
        if 'si' in disasm.lower() or 'di' in disasm.lower():
            has_si_di = True
    
    return {
        'address': func_addr,
        'name': idc.get_func_name(func_addr),
        'size': size,
        'callees': callees,
        'callers': callers,
        'num_callees': len(callees),
        'num_callers': len(callers),
        'has_loop': has_loop,
        'has_far_call': has_far_call,
        'cmp_count': cmp_count,
        'has_si_di': has_si_di,
        'is_leaf': len(callees) == 0
    }

def categorize_function(sig):
    """Categorize function based on signature."""
    categories = []
    
    # Leaf functions
    if sig['is_leaf']:
        categories.append('leaf')
        if sig['cmp_count'] > 3:
            categories.append('dispatcher')  # Pure computation with comparisons
        else:
            categories.append('calculator')  # Simple calculation
    
    # Size-based
    if sig['size'] < 20:
        categories.append('tiny')
    elif sig['size'] < 50:
        categories.append('small')
    else:
        categories.append('medium')
    
    # Pattern-based
    if sig['has_si_di']:
        categories.append('array_iterator')
    if sig['has_loop']:
        categories.append('looping')
    if sig['has_far_call']:
        categories.append('cross_segment')
    
    # Call pattern
    if sig['num_callers'] > 5:
        categories.append('widely_used')
    elif sig['num_callers'] == 1:
        categories.append('specialized')
    
    return categories

def suggest_name(sig, categories):
    """Suggest a function name based on signature and categories."""
    
    # Look at what it calls for clues
    callee_hints = []
    for callee in sig['callees']:
        if 'angle' in callee or 'heading' in callee:
            callee_hints.append('angle')
        if 'terrain' in callee or 'tile' in callee:
            callee_hints.append('terrain')
        if 'vector' in callee or 'vec' in callee:
            callee_hints.append('vector')
        if 'fixed' in callee or 'mul' in callee:
            callee_hints.append('math')
        if 'state' in callee or 'flag' in callee:
            callee_hints.append('state')
    
    # Look at who calls it
    caller_hints = []
    for caller in sig['callers']:
        if 'behavior' in caller or 'state_machine' in caller:
            caller_hints.append('behavior')
        if 'tracking' in caller or 'target' in caller:
            caller_hints.append('tracking')
        if 'mirror' in caller:
            caller_hints.append('sync')
    
    # Build suggested name
    prefix = "ai"
    
    # Component
    component = "helper"
    if 'angle' in callee_hints:
        component = "angle"
    elif 'terrain' in callee_hints:
        component = "position"
    elif 'vector' in callee_hints or 'math' in callee_hints:
        component = "vector"
    elif 'state' in callee_hints:
        component = "state"
    elif 'behavior' in caller_hints:
        component = "behavior"
    elif 'tracking' in caller_hints:
        component = "tracking"
    elif 'sync' in caller_hints:
        component = "sync"
    
    # Action
    action = "helper"
    if 'leaf' in categories and 'dispatcher' in categories:
        action = "check"
    elif 'leaf' in categories:
        action = "get" if sig['size'] < 20 else "calc"
    elif 'looping' in categories or 'array_iterator' in categories:
        action = "update"
    
    suggested = f"{prefix}_{component}_{action}"
    
    # Add confidence
    confidence = "low"
    if callee_hints or caller_hints:
        confidence = "medium"
    if len(callee_hints) > 1 or len(caller_hints) > 1:
        confidence = "high"
    
    return suggested, confidence, callee_hints, caller_hints

def main():
    print("="*80)
    print("BATCH ANALYZING REMAINING AI HELPER FUNCTIONS")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    # Load the callees report to get the list
    report_path = Path(__file__).parent.parent / "ai_callees_report.json"
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    # Get remaining functions
    remaining = []
    for func in report['new_functions']:
        addr = func['address']
        if addr not in ALREADY_NAMED:
            remaining.append(addr)
    
    # Remove duplicates (functions called by multiple targets)
    remaining = list(set(remaining))
    
    print(f"\nAnalyzing {len(remaining)} remaining AI functions...")
    
    # Analyze each
    results = []
    for addr in sorted(remaining):
        sig = get_function_signature(addr)
        if sig:
            categories = categorize_function(sig)
            suggested_name, confidence, callee_hints, caller_hints = suggest_name(sig, categories)
            
            sig['categories'] = categories
            sig['suggested_name'] = suggested_name
            sig['confidence'] = confidence
            sig['callee_hints'] = callee_hints
            sig['caller_hints'] = caller_hints
            
            results.append(sig)
            
            print(f"  {sig['name']:30} -> {suggested_name:40} [{confidence:6}] {sig['size']:3}B")
    
    # Group by suggested name prefix
    print(f"\n{'='*80}")
    print("GROUPING BY SUGGESTED NAME")
    print("="*80)
    
    grouped = {}
    for r in results:
        prefix = '_'.join(r['suggested_name'].split('_')[:2])  # e.g., "ai_angle"
        if prefix not in grouped:
            grouped[prefix] = []
        grouped[prefix].append(r)
    
    for prefix in sorted(grouped.keys()):
        funcs = grouped[prefix]
        print(f"\n{prefix.upper()} ({len(funcs)} functions):")
        for f in sorted(funcs, key=lambda x: x['size'], reverse=True):
            print(f"  {f['address']:#08x}: {f['name']:30} ({f['size']:3}B) -> {f['suggested_name']} [{f['confidence']}]")
            if f['callee_hints']:
                print(f"           Calls: {', '.join(f['callees'][:3])}")
            if f['caller_hints']:
                print(f"           Called by: {', '.join(f['callers'][:3])}")
    
    # Save results
    output_path = Path(__file__).parent.parent / "ai_helpers_batch_analysis.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Analysis saved to: {output_path}")
    print(f"Total functions analyzed: {len(results)}")
    print("="*80)
    
    # Statistics
    by_confidence = {}
    for r in results:
        conf = r['confidence']
        by_confidence[conf] = by_confidence.get(conf, 0) + 1
    
    print(f"\nConfidence levels:")
    for conf in ['high', 'medium', 'low']:
        count = by_confidence.get(conf, 0)
        print(f"  {conf:8}: {count:3} functions")
    
    # Exit
    idc.qexit(0)

if __name__ == "__main__":
    main()
