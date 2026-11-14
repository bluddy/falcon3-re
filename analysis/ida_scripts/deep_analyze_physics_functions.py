"""
Deep analysis of Flight Physics functions - analyze top candidates in detail
to find naming patterns and potentially expand further.

Usage:
    idat.exe -A -S"deep_analyze_physics_functions.py" FALCONCD.EXE.i64
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path
from collections import defaultdict

def load_target_functions():
    """Load new functions from the callees report."""
    report_path = Path(__file__).parent.parent / "flight_physics_callees_report.json"
    
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    # Get all new functions
    targets = []
    for func in data['new_functions']:
        targets.append({
            'address': func['address'],
            'name': func['name'],
            'size': func['size'],
            'caller_count': func['caller_count'],
            'called_by': func['called_by']
        })
    
    print(f"Loaded {len(targets)} target functions from report")
    return targets

def analyze_function_detailed(func_addr):
    """Perform detailed analysis of a function."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    analysis = {
        'address': func_addr,
        'name': idc.get_func_name(func_addr),
        'size': func.end_ea - func.start_ea,
        'instructions': [],
        'registers_used': set(),
        'calls': [],
        'xrefs_to': [],
        'data_refs': [],
        'comparison_count': 0,
        'loop_indicators': 0
    }
    
    # Analyze instructions
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head)
        op1 = idc.print_operand(head, 0)
        op2 = idc.print_operand(head, 1)
        
        analysis['instructions'].append({
            'ea': head,
            'mnem': mnem,
            'op1': op1,
            'op2': op2
        })
        
        # Track register usage
        for reg in ['ax', 'bx', 'cx', 'dx', 'si', 'di', 'bp', 'sp']:
            if reg in op1.lower() or reg in op2.lower():
                analysis['registers_used'].add(reg)
        
        # Count comparisons/branches
        if mnem in ['cmp', 'test', 'jz', 'jnz', 'je', 'jne', 'jl', 'jg', 'jle', 'jge', 'ja', 'jb', 'jae', 'jbe', 'jcxz']:
            analysis['comparison_count'] += 1
        
        # Detect loops
        if mnem in ['loop', 'loope', 'loopne', 'loopnz', 'loopz']:
            analysis['loop_indicators'] += 1
        elif mnem.startswith('j'):  # Jump backwards = loop
            target_ea = idc.get_operand_value(head, 0)
            if target_ea < head:
                analysis['loop_indicators'] += 1
        
        # Track function calls
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                target_func = idaapi.get_func(xref.to)
                if target_func:
                    analysis['calls'].append({
                        'ea': xref.to,
                        'name': idc.get_func_name(xref.to)
                    })
        
        # Track data references
        for xref in idautils.DataRefsFrom(head):
            analysis['data_refs'].append(xref)
    
    # Convert sets to lists for JSON
    analysis['registers_used'] = sorted(list(analysis['registers_used']))
    
    # Get callers
    for xref in idautils.XrefsTo(func_addr, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                analysis['xrefs_to'].append({
                    'ea': caller_func.start_ea,
                    'name': idc.get_func_name(caller_func.start_ea)
                })
    
    return analysis

def categorize_function(analysis):
    """Categorize function based on patterns."""
    size = analysis['size']
    comp_count = analysis['comparison_count']
    calls = len(analysis['calls'])
    callers = len(analysis['xrefs_to'])
    loops = analysis['loop_indicators']
    
    categories = []
    confidence = "LOW"
    suggested_name = analysis['name']
    reasoning = []
    
    # Size-based categorization
    if size >= 300:
        categories.append("LARGE_COORDINATOR")
        reasoning.append(f"Large function ({size}B) suggests coordinator/sequencer")
    elif size >= 100:
        categories.append("MEDIUM_LOGIC")
        reasoning.append(f"Medium size ({size}B) suggests specific behavior")
    elif size <= 30:
        categories.append("TINY_HELPER")
        reasoning.append(f"Tiny size ({size}B) suggests helper/accessor")
        if callers >= 3:
            confidence = "MEDIUM"
            reasoning.append(f"Used by {callers} functions - likely utility")
    
    # Complexity indicators
    if comp_count > 15:
        categories.append("HIGH_BRANCHING")
        reasoning.append(f"{comp_count} comparisons = complex decision logic")
    elif comp_count == 0 and size > 20:
        categories.append("STRAIGHT_LINE")
        reasoning.append("No branches = straight-line computation")
        confidence = "MEDIUM"
    
    # Call patterns
    if calls == 0 and size > 10:
        categories.append("LEAF_FUNCTION")
        reasoning.append(f"No calls = leaf function (primitive operation)")
        if callers >= 3:
            confidence = "HIGH"
            reasoning.append(f"{callers} callers use this primitive")
    
    # Loop detection
    if loops > 0:
        categories.append("ITERATIVE")
        reasoning.append(f"{loops} loop indicators = iterative processing")
    
    # Register patterns (physics often uses SI/DI for data access)
    if 'si' in analysis['registers_used'] and 'di' in analysis['registers_used']:
        categories.append("DUAL_POINTER")
        reasoning.append("SI+DI usage suggests dual data access")
    
    return {
        'categories': categories,
        'confidence': confidence,
        'reasoning': reasoning
    }

def main():
    print("="*80)
    print("DEEP ANALYSIS OF FLIGHT PHYSICS FUNCTIONS")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    # Load targets
    targets = load_target_functions()
    
    # Analyze top 15 by size (coordinators)
    print("\n" + "="*80)
    print("ANALYZING TOP 15 BY SIZE (COMPLEXITY CANDIDATES)")
    print("="*80)
    
    by_size = sorted(targets, key=lambda x: x['size'], reverse=True)[:15]
    
    detailed_results = []
    
    for i, target in enumerate(by_size, 1):
        addr = target['address']
        print(f"\n[{i}/15] Analyzing {target['name']} @ {addr:#08x} ({target['size']}B)...")
        
        analysis = analyze_function_detailed(addr)
        if analysis:
            categorization = categorize_function(analysis)
            analysis['categorization'] = categorization
            detailed_results.append(analysis)
            
            print(f"  Categories: {', '.join(categorization['categories'])}")
            print(f"  Confidence: {categorization['confidence']}")
            print(f"  Calls: {len(analysis['calls'])} functions")
            print(f"  Called by: {len(analysis['xrefs_to'])} functions")
            print(f"  Reasoning:")
            for reason in categorization['reasoning']:
                print(f"    - {reason}")
    
    # Save results
    output_path = Path(__file__).parent.parent / "flight_physics_deep_analysis.json"
    
    report = {
        'timestamp': '2026-11-15',
        'total_analyzed': len(detailed_results),
        'functions': detailed_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Deep analysis saved to: {output_path}")
    print(f"Analyzed {len(detailed_results)} functions in detail")
    print("="*80)
    
    # Exit
    idc.qexit(0)

if __name__ == "__main__":
    main()
