import idaapi
import idautils
import idc
import json

# Wait for auto-analysis
idaapi.auto_wait()

print("[*] Extracting Path B unique functions from r15_simulation_loop...")

# Path B unique functions identified from analysis
path_b_functions = [
    (0x205BF, "stub_to_205c3"),
    (0x207DD, "undoc_207DD"),
    (0x128CD, "sub_128CD"),
    (0x109660, "undoc_109660"),
    (0x12910, "sub_12910"),
    (0x1FE68, "sub_1FE68"),
    (0x1FE6F, "sub_1FE6F"),
    (0x210FE, "sub_210FE"),
    (0x1FF5D, "sub_1FF5D"),
    (0x21240, "sub_21240"),
    (0x20BCE, "sub_20BCE"),
    # Also extract the far pointer save/restore functions
    (0x1F0C0, "active_farptr_set"),
    (0x1F0D7, "active_farptr_restore"),
]

results = []

for addr, name in path_b_functions:
    print(f"\n[*] Analyzing {name} @ 0x{addr:X}")
    
    func = idaapi.get_func(addr)
    if not func:
        print(f"  [!] No function found at 0x{addr:X}")
        continue
    
    # Get current name from IDA
    current_name = idc.get_func_name(addr)
    
    # Extract instructions
    instructions = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        if idc.is_code(idc.get_full_flags(head)):
            disasm = idc.generate_disasm_line(head, 0)
            instructions.append({
                'addr': f'0x{head:X}',
                'disasm': disasm
            })
    
    # Get callers
    callers = []
    for xref in idautils.XrefsTo(addr):
        if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
            caller_name = idc.get_func_name(xref.frm)
            callers.append({
                'addr': f'0x{xref.frm:X}',
                'name': caller_name
            })
    
    # Get callees
    callees = []
    for head in idautils.Heads(func.start_ea, func.end_ea):
        for xref in idautils.XrefsFrom(head, 0):
            if xref.type in [idaapi.fl_CN, idaapi.fl_CF]:
                callee_name = idc.get_func_name(xref.to)
                if callee_name and callee_name != current_name:
                    callees.append({
                        'addr': f'0x{xref.to:X}',
                        'name': callee_name
                    })
    
    result = {
        'expected_name': name,
        'current_name': current_name,
        'address': f'0x{addr:X}',
        'size': func.end_ea - func.start_ea,
        'instruction_count': len(instructions),
        'instructions': instructions,
        'caller_count': len(callers),
        'callers': callers[:10],
        'callee_count': len(callees),
        'callees': list({c['name']: c for c in callees}.values())[:10]
    }
    
    results.append(result)
    
    print(f"  Size: {result['size']} bytes")
    print(f"  Instructions: {len(instructions)}")
    print(f"  Callers: {len(callers)}")
    print(f"  Callees: {len(callees)}")
    
    # Save individual file
    output_path = rf'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\path_b_{addr:x}_full.json'
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"  Saved to path_b_{addr:x}_full.json")

# Save batch
batch_path = r'c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\path_b_functions_analysis.json'
with open(batch_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n[+] Path B function analysis complete: {batch_path}")
print(f"[+] Extracted {len(results)} functions")

# Exit IDA
idc.qexit(0)
