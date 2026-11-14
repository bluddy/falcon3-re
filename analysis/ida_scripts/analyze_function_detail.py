"""
Analyze specific functions in detail to understand their purpose.

This script examines functions to extract:
- Disassembly with comments
- Data references
- String references
- Call patterns
- Memory access patterns

Usage:
    idat.exe -A -S"analyze_function_detail.py" FALCONCD.EXE.i64
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

# Top candidates from callee analysis (large, frequently called)
TARGET_FUNCTIONS = [
    # Large complex functions
    (0x3D37F, "sub_3D37F", 1319),  # Largest - probably main AI handler
    (0x3CF9D, "sub_3CF9D", 886),   # Called by all state machine functions
    (0x3F3A8, "sub_3F3A8", 256),   # Medium size AI function
    (0x49997, "sub_49997", 130),   # Called by batch processor
    (0x407C0, "sub_407C0", 131),   # AI state function
    (0x423A9, "sub_423A9", 178),   # AI behavior
    (0x40884, "sub_40884", 99),    # AI helper
    (0x3EB4E, "sub_3EB4E", 87),    # Mid-size helper
    (0x425A2, "sub_425A2", 88),    # Called by state machine
    (0x42503, "sub_42503", 80),    # AI behavior helper
]

def get_string_refs(func_addr):
    """Find string references in a function."""
    strings = []
    func = idaapi.get_func(func_addr)
    if not func:
        return strings
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        # Check for data references
        for dref in idautils.DataRefsFrom(head):
            # Check if it's a string
            str_type = idc.get_str_type(dref)
            if str_type is not None:
                string_val = idc.get_strlit_contents(dref)
                if string_val:
                    strings.append({
                        'address': dref,
                        'value': string_val.decode('ascii', errors='ignore'),
                        'ref_from': head
                    })
    
    return strings

def get_data_refs(func_addr):
    """Find data references in a function."""
    data_refs = []
    func = idaapi.get_func(func_addr)
    if not func:
        return data_refs
    
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for dref in idautils.DataRefsFrom(head):
            # Skip strings (handled separately)
            if idc.get_str_type(dref) is None:
                data_name = idc.get_name(dref)
                if data_name:
                    data_refs.append({
                        'address': dref,
                        'name': data_name,
                        'ref_from': head
                    })
    
    return data_refs

def get_key_instructions(func_addr, max_lines=50):
    """Get key instructions from function (first N lines)."""
    instructions = []
    func = idaapi.get_func(func_addr)
    if not func:
        return instructions
    
    count = 0
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if count >= max_lines:
            break
        
        disasm = idc.generate_disasm_line(head, 0)
        mnem = idc.print_insn_mnem(head)
        
        # Mark interesting instructions
        interesting = False
        note = ""
        
        if mnem in ['call', 'jmp']:
            target = idc.get_operand_value(head, 0)
            target_name = idc.get_func_name(target) if target else None
            if target_name:
                note = f"-> {target_name}"
                interesting = True
        elif mnem in ['cmp', 'test']:
            interesting = True
            note = "comparison"
        elif 'word ptr' in disasm or 'byte ptr' in disasm:
            # Memory access
            interesting = True
            note = "memory access"
        
        instructions.append({
            'address': head,
            'offset': head - func.start_ea,
            'mnem': mnem,
            'disasm': disasm,
            'interesting': interesting,
            'note': note
        })
        
        count += 1
    
    return instructions

def get_callees(func_addr):
    """Get functions called by this function."""
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
                        'name': idc.get_func_name(target_func.start_ea),
                        'call_site': head
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
                    'name': idc.get_func_name(caller_func.start_ea),
                    'call_site': xref.frm
                })
    
    return callers

def analyze_function(func_addr, func_name, func_size):
    """Perform detailed analysis of a function."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {func_name} @ {func_addr:#08x} ({func_size} bytes)")
    print(f"{'='*80}")
    
    func = idaapi.get_func(func_addr)
    if not func:
        print("  ERROR: Not a valid function!")
        return None
    
    # Get analysis data
    strings = get_string_refs(func_addr)
    data_refs = get_data_refs(func_addr)
    instructions = get_key_instructions(func_addr, max_lines=30)
    callees = get_callees(func_addr)
    callers = get_callers(func_addr)
    
    # Print summary
    print(f"\nStrings referenced: {len(strings)}")
    for s in strings[:5]:  # Show first 5
        print(f"  '{s['value']}' @ {s['address']:#08x}")
    
    print(f"\nData references: {len(data_refs)}")
    for d in data_refs[:10]:  # Show first 10
        print(f"  {d['name']} @ {d['address']:#08x}")
    
    print(f"\nCalls {len(callees)} functions:")
    for c in callees[:10]:
        print(f"  -> {c['name']}")
    
    print(f"\nCalled by {len(callers)} functions:")
    for c in callers[:10]:
        print(f"  <- {c['name']}")
    
    print(f"\nKey instructions (first 30):")
    for i, inst in enumerate(instructions):
        if inst['interesting']:
            print(f"  +{inst['offset']:04x}: {inst['disasm']:60} ; {inst['note']}")
        elif i < 10:  # Show first 10 always
            print(f"  +{inst['offset']:04x}: {inst['disasm']}")
    
    # Analyze patterns
    patterns = []
    
    # Check for loop patterns
    loop_count = sum(1 for i in instructions if i['mnem'] in ['loop', 'loope', 'loopne'])
    if loop_count > 0:
        patterns.append(f"Contains {loop_count} loop(s)")
    
    # Check for array access patterns
    if any('si' in i['disasm'] or 'di' in i['disasm'] for i in instructions):
        patterns.append("Array/memory iteration (SI/DI)")
    
    # Check for comparison chains (state machine?)
    cmp_count = sum(1 for i in instructions if i['mnem'] in ['cmp', 'test'])
    if cmp_count > 5:
        patterns.append(f"Many comparisons ({cmp_count}) - likely state machine or dispatch")
    
    # Check for far calls (overlay/segment access)
    far_calls = sum(1 for i in instructions if 'far ptr' in i['disasm'])
    if far_calls > 0:
        patterns.append(f"Far calls ({far_calls}) - cross-segment access")
    
    if patterns:
        print(f"\nDetected patterns:")
        for p in patterns:
            print(f"  • {p}")
    
    return {
        'address': func_addr,
        'name': func_name,
        'size': func_size,
        'strings': strings,
        'data_refs': data_refs,
        'instructions': instructions,
        'callees': callees,
        'callers': callers,
        'patterns': patterns
    }

def main():
    print("="*80)
    print("DETAILED FUNCTION ANALYSIS")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    results = {}
    
    for func_addr, func_name, func_size in TARGET_FUNCTIONS:
        result = analyze_function(func_addr, func_name, func_size)
        if result:
            results[func_name] = result
    
    # Save detailed report
    output_path = Path(__file__).parent.parent / "ai_function_analysis_detailed.json"
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Detailed analysis saved to: {output_path}")
    print(f"{'='*80}")
    
    # Summary insights
    print(f"\nQuick Insights:")
    print(f"-" * 80)
    
    for name, result in results.items():
        print(f"\n{name}:")
        print(f"  Size: {result['size']}B")
        print(f"  Calls: {len(result['callees'])} functions")
        print(f"  Called by: {len(result['callers'])} functions")
        if result['strings']:
            print(f"  Strings: {len(result['strings'])} (debug messages?)")
        if result['patterns']:
            print(f"  Patterns: {', '.join(result['patterns'])}")
    
    # Exit
    idc.qexit(0)

if __name__ == "__main__":
    main()
