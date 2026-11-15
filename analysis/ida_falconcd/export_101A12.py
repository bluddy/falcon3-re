import ida_auto
import ida_funcs
import ida_xref
import idc
import json
import sys

ida_auto.auto_wait()

addr = 0x101A12
func = ida_funcs.get_func(addr)

if not func:
    print(f"ERROR: No function at 0x{addr:X}", file=sys.stderr)
    idc.qexit(1)

# Basic info
result = {
    'address': f'0x{addr:X}',
    'name': idc.get_func_name(addr),
    'size': func.end_ea - func.start_ea,
    'start': f'0x{func.start_ea:X}',
    'end': f'0x{func.end_ea:X}'
}

# Count callers
callers = []
for xref in ida_xref.XrefsTo(addr, 0):
    if xref.type in [ida_xref.fl_CN, ida_xref.fl_CF]:
        callers.append(xref.frm)

result['caller_count'] = len(set(callers))
result['sample_callers'] = []
for caller_addr in list(set(callers))[:50]:
    caller_func = ida_funcs.get_func(caller_addr)
    if caller_func:
        result['sample_callers'].append({
            'addr': f'0x{caller_func.start_ea:X}',
            'name': idc.get_func_name(caller_func.start_ea)
        })

# Count callees
callees = []
for head in ida_funcs.FuncItems(addr):
    for xref in ida_xref.XrefsFrom(head, 0):
        if xref.type in [ida_xref.fl_CN, ida_xref.fl_CF]:
            callees.append(xref.to)

unique_callees = list(set(callees))
result['callee_count'] = len(unique_callees)
result['all_callees'] = []
for callee_addr in unique_callees:
    result['all_callees'].append({
        'addr': f'0x{callee_addr:X}',
        'name': idc.get_func_name(callee_addr)
    })

# Get disassembly
result['disassembly'] = []
ea = func.start_ea
while ea < func.end_ea:
    result['disassembly'].append({
        'addr': f'0x{ea:X}',
        'insn': idc.GetDisasm(ea)
    })
    ea = idc.next_head(ea, func.end_ea)

# Save
output_file = r"c:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\sub_101A12_analysis.json"
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)

print(f"SUCCESS: {output_file}")
idc.qexit(0)
