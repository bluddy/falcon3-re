"""
Dump disassembly of specific Flight Physics functions for manual naming.

Usage:
    idat.exe -A -S"dump_physics_disasm.py" FALCONCD.EXE.i64
"""

import idc
import idaapi
import idautils
import json
from pathlib import Path

# Priority functions to analyze (HIGH/MEDIUM confidence + high usage)
TARGET_FUNCTIONS = [
    # HIGH confidence (leaf, straight-line, 3 callers)
    0x4D35A,  # sub_4D35A: 50B, STRAIGHT_LINE, LEAF_FUNCTION, 3 callers
    
    # MEDIUM confidence (leaf, straight-line, 2 callers)
    0x4D38C,  # sub_4D38C: 59B, STRAIGHT_LINE, LEAF_FUNCTION, 2 callers
    
    # High usage utilities
    0x445A6,  # sub_445A6: 105B, 7 callers - most used!
    0x3B5D1,  # sub_3B5D1: 10B, 5 callers - tiny utility
    0x3B72C,  # sub_3B72C: 16B, 5 callers - tiny utility
    0x3B6E2,  # sub_3B6E2: 74B, 3 callers
    0x2C121,  # sub_2C121: 8B, 3 callers - tiny!
    0x3B503,  # sub_3B503: 70B, 3 callers
    
    # Medium/small with 2 callers
    0x4478D,  # sub_4478D: 222B, 2 callers, 27 comparisons
    0x3B256,  # sub_3B256: 201B, 2 callers
    0x3B5DB,  # sub_3B5DB: 14B, 2 callers
    
    # Large coordinators (1 caller but complex)
    0x496D3,  # sub_496D3: 538B, 34 comparisons
    0x4D55F,  # sub_4D55F: 512B, 24 comparisons
]

def dump_function_disasm(func_addr):
    """Dump complete disassembly of a function with context."""
    func = idaapi.get_func(func_addr)
    if not func:
        return None
    
    result = {
        'address': func_addr,
        'name': idc.get_func_name(func_addr),
        'size': func.end_ea - func.start_ea,
        'disasm': [],
        'calls': [],
        'called_by': []
    }
    
    # Get disassembly
    for head in idautils.Heads(func.start_ea, func.end_ea):
        mnem = idc.print_insn_mnem(head)
        disasm_line = idc.generate_disasm_line(head, 0)
        
        result['disasm'].append({
            'ea': head,
            'offset': head - func.start_ea,
            'mnem': mnem,
            'line': disasm_line
        })
        
        # Track calls
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                target_func = idaapi.get_func(xref.to)
                if target_func:
                    target_name = idc.get_func_name(xref.to)
                    if target_name not in [c['name'] for c in result['calls']]:
                        result['calls'].append({
                            'ea': xref.to,
                            'name': target_name
                        })
    
    # Get callers
    for xref in idautils.XrefsTo(func_addr, 0):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_func = idaapi.get_func(xref.frm)
            if caller_func:
                caller_name = idc.get_func_name(caller_func.start_ea)
                if caller_name not in [c['name'] for c in result['called_by']]:
                    result['called_by'].append({
                        'ea': caller_func.start_ea,
                        'name': caller_name,
                        'call_site': xref.frm
                    })
    
    return result

def format_disasm_text(func_data):
    """Format disassembly as readable text."""
    lines = []
    lines.append("="*80)
    lines.append(f"Function: {func_data['name']} @ {func_data['address']:#08x}")
    lines.append(f"Size: {func_data['size']} bytes")
    lines.append(f"Calls: {len(func_data['calls'])} functions")
    lines.append(f"Called by: {len(func_data['called_by'])} functions")
    lines.append("="*80)
    
    if func_data['calls']:
        lines.append("\nCALLS:")
        for call in func_data['calls']:
            lines.append(f"  {call['ea']:#08x}: {call['name']}")
    
    if func_data['called_by']:
        lines.append("\nCALLED BY:")
        for caller in func_data['called_by']:
            lines.append(f"  {caller['ea']:#08x}: {caller['name']} (call site: {caller['call_site']:#08x})")
    
    lines.append("\nDISASSEMBLY:")
    lines.append("-"*80)
    
    for insn in func_data['disasm']:
        lines.append(f"{insn['ea']:#08x} (+{insn['offset']:3x}): {insn['line']}")
    
    lines.append("="*80)
    lines.append("")
    
    return "\n".join(lines)

def main():
    print("="*80)
    print("DUMPING FLIGHT PHYSICS FUNCTION DISASSEMBLY")
    print("="*80)
    
    # Wait for auto-analysis
    print("\nWaiting for auto-analysis...")
    idaapi.auto_wait()
    
    print(f"\nDumping {len(TARGET_FUNCTIONS)} priority functions...\n")
    
    all_dumps = []
    text_output = []
    
    for i, func_addr in enumerate(TARGET_FUNCTIONS, 1):
        print(f"[{i}/{len(TARGET_FUNCTIONS)}] Dumping {func_addr:#08x}...")
        
        func_data = dump_function_disasm(func_addr)
        if func_data:
            all_dumps.append(func_data)
            text_output.append(format_disasm_text(func_data))
        else:
            print(f"  WARNING: {func_addr:#08x} is not a function!")
    
    # Save JSON
    json_path = Path(__file__).parent.parent / "flight_physics_disasm.json"
    with open(json_path, 'w') as f:
        json.dump({
            'timestamp': '2026-11-15',
            'total_functions': len(all_dumps),
            'functions': all_dumps
        }, f, indent=2, default=str)
    
    # Save text
    text_path = Path(__file__).parent.parent / "flight_physics_disasm.txt"
    with open(text_path, 'w') as f:
        f.write('\n'.join(text_output))
    
    print(f"\n{'='*80}")
    print(f"Disassembly dumps saved:")
    print(f"  JSON: {json_path}")
    print(f"  TEXT: {text_path}")
    print(f"Total functions dumped: {len(all_dumps)}")
    print("="*80)
    
    # Exit
    idc.qexit(0)

if __name__ == "__main__":
    main()
