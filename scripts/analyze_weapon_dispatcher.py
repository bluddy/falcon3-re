import idc
import idautils
import idaapi
import json

def disassemble_function(ea, max_lines=300):
    """Disassemble a function"""
    result = []
    func = idaapi.get_func(ea)
    if not func:
        return result
    
    current = func.start_ea
    line_count = 0
    while current < func.end_ea and line_count < max_lines:
        disasm = idc.generate_disasm_line(current, 0)
        
        # Get data references
        data_refs = []
        for ref in idautils.DataRefsFrom(current):
            seg = idaapi.getseg(ref)
            if seg and seg.type == idaapi.SEG_DATA:
                ref_name = idc.get_name(ref)
                if not ref_name:
                    ref_name = f"ds_{ref:X}"
                data_refs.append({
                    'address': hex(ref),
                    'name': ref_name
                })
        
        result.append({
            'ea': hex(current),
            'disasm': disasm,
            'data_refs': data_refs if data_refs else None
        })
        current = idc.next_head(current)
        line_count += 1
    
    return result

def find_callers(target_ea):
    """Find all functions that call a target function"""
    callers = []
    for xref in idautils.XrefsTo(target_ea, idaapi.XREF_ALL):
        func = idaapi.get_func(xref.frm)
        if func:
            func_name = idc.get_func_name(func.start_ea)
            if func_name:
                callers.append({
                    'function': func_name,
                    'address': hex(func.start_ea),
                    'call_site': hex(xref.frm)
                })
    return callers

print("Analyzing weapon dispatcher...")

# Analyze r05_farptr_dispatch_big
dispatcher_ea = 0x3DA56
dispatcher_disasm = disassemble_function(dispatcher_ea)

# Find who calls the dispatcher
dispatcher_callers = find_callers(dispatcher_ea)

# Analyze each caller
caller_analysis = {}
for caller in dispatcher_callers:
    caller_ea = int(caller['address'], 16)
    caller_disasm = disassemble_function(caller_ea, max_lines=150)
    caller_analysis[caller['function']] = {
        'address': caller['address'],
        'call_site': caller['call_site'],
        'disasm': caller_disasm
    }

results = {
    'dispatcher': {
        'address': hex(dispatcher_ea),
        'name': 'r05_farptr_dispatch_big',
        'disasm': dispatcher_disasm
    },
    'callers': dispatcher_callers,
    'caller_analysis': caller_analysis
}

with open('weapon_dispatcher_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Dispatcher at {hex(dispatcher_ea)}")
print(f"Found {len(dispatcher_callers)} callers:")
for caller in dispatcher_callers:
    print(f"  {caller['function']} at {caller['address']}")

idc.qexit(0)
