import idaapi
import idautils
import idc
import ida_funcs
import json

func_ea = 0x34C31
func = ida_funcs.get_func(func_ea)

result = {
    'function': {
        'address': hex(func_ea),
        'name': idc.get_func_name(func_ea),
        'size': func.end_ea - func.start_ea
    },
    'analysis': 'Brief analysis of mode_axis_state_select',
    'globals_accessed': [],
    'key_checks': []
}

# Find key byte/word comparisons (state checks)
for ea in idautils.Heads(func.start_ea, func.end_ea):
    mnem = idc.print_insn_mnem(ea)
    if mnem == 'cmp':
        op1 = idc.print_operand(ea, 0)
        op2 = idc.print_operand(ea, 1)
        if 'ds:' in op1 or 'byte ptr' in op1 or 'word ptr' in op1:
            result['key_checks'].append({
                'address': hex(ea),
                'check': f"{op1} vs {op2}",
                'disasm': idc.generate_disasm_line(ea, 0)
            })

# Find key globals
for ea in idautils.Heads(func.start_ea, func.end_ea):
    for i in range(2):
        op_type = idc.get_operand_type(ea, i)
        if op_type == idc.o_mem:
            mem_addr = idc.get_operand_value(ea, i)
            mem_name = idc.get_name(mem_addr) or hex(mem_addr)
            if mem_name not in [g['name'] for g in result['globals_accessed']]:
                result['globals_accessed'].append({
                    'address': hex(mem_addr),
                    'name': mem_name,
                    'first_use': hex(ea)
                })

print(f"=== {result['function']['name']} ===")
print(f"Address: {result['function']['address']}")
print(f"Size: {result['function']['size']} bytes")
print(f"\n=== KEY STATE CHECKS (first 10) ===")
for check in result['key_checks'][:10]:
    print(f"  {check['address']}: {check['check']}")

print(f"\n=== KEY GLOBALS (first 10) ===")
for g in result['globals_accessed'][:10]:
    print(f"  {g['name']} ({g['address']})")

# Save
output_file = r'C:\Users\ybarnoy\projects\falcon3\analysis\ida_falconcd\mode_axis_34c31_brief.json'
with open(output_file, 'w') as f:
    json.dump(result, f, indent=2)

print(f"\n✓ Saved to: {output_file}")

idc.qexit(0)
